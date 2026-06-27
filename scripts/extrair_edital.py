#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extrai o conteúdo programático de um edital para JSON canônico, com SELEÇÃO DE CARGO.

Editais de concurso normalmente trazem: CONHECIMENTOS GERAIS (comuns a todos) +
CONHECIMENTOS ESPECÍFICOS por cargo/especialidade. Este script detecta os cargos e
monta a saída como: Gerais + Específicos do cargo escolhido.

Uso:
  # 1) listar cargos detectados
  python3 extrair_edital.py edital.pdf --listar

  # 2) gerar JSON de um cargo (por número ou trecho do nome)
  python3 extrair_edital.py edital.pdf --cargo "Sem especialidade" --out edital.json
  python3 extrair_edital.py edital.pdf --cargo 1 --out edital.json

  # .md verticalizado (formato da skill `verticalizar-edital`): extração exata, cargo único
  python3 extrair_edital.py edital.md --out edital.json
"""
import argparse, json, re, sys, unicodedata
from pathlib import Path

DISC_MD  = re.compile(r'^#\s+(\d+)\.\s+(.+\S)\s*$')
ASSUNTO  = re.compile(r'^#{2,3}\s+(\d+(?:\.\d+)*)\s+(.+\S)\s*$')
NUMITEM  = re.compile(r'^\s*[-*•]?\s*(\d+(?:\.\d+)*)[\).]?\s+(.+\S)\s*$')
META     = re.compile(r'^\*\*(.+?):\*\*\s*(.*\S)\s*$')
TITLE_H1 = re.compile(r'^#\s+(.+\S)\s*$')
META_MAP = {"órgão": "orgao", "orgao": "orgao", "banca": "banca", "cargo": "cargo",
            "data do edital": "data_edital", "data": "data_edital", "concurso": "concurso"}

PAGE_NOISE = re.compile(r'TRIBUNAL DE JUSTI|CONCURSO P[ÚU]BLICO|^\s*\d{1,3}\s*$|^\s*P[áa]gina\s+\d+', re.I)
ITEM_MARK  = re.compile(r'(?<![\w./º°§])(\d{1,2}(?:\.\d{1,2}){0,3})\s+(?=[A-ZÀ-Ý])')
PRECEDE_BAD = re.compile(r'(n[ºo°]\.?|lei|decreto|resolu|s[úu]mula|\bart|§|inciso|\bn\b)\s*$', re.I)

HEADER_WORDS = {"CARGO", "GRUPO", "NIVEL", "SUPERIOR", "MEDIO", "SEM", "COM", "E", "DA", "DE",
                "DO", "DOS", "DAS", "ESPECIALIDADE", "ANALISTA", "TECNICO", "JUDICIARIO",
                "ASSISTENCIAL", "JUDICIAL", "GESTAO", "TECNOLOGIA", "INFORMACAO", "OFICIAL"}
SECTION_SKIP = ("ANEXO", "CONTEUDO PROGRAM")


def _fold(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").upper()


def _add(disc, numero, texto):
    disc["itens"].append({"numero": numero, "nivel": numero.count(".") + 1, "texto": texto.strip()})


def _is_caps_header(s):
    s = s.strip()
    if len(s) < 3 or len(s) > 75 or s[0].isdigit():
        return False
    letters = [c for c in s if c.isalpha()]
    return len(letters) >= 3 and (sum(c.isupper() for c in letters) / len(letters)) > 0.85


def _is_section(s):
    u = _fold(s)
    return any(k in u for k in SECTION_SKIP)


def _is_header_fragment(s):
    toks = re.findall(r"[A-Za-zÀ-ÿ]+", s)
    return bool(toks) and all(_fold(t) in HEADER_WORDS for t in toks)


def _cargo_name(buf_text):
    u = _fold(buf_text)
    if "ESPECIALIDADE" in u:
        after = re.split(r'(?i)especialidade\s*:?\s*', buf_text)[-1].strip(" –-:.")
        if after and _fold(after) not in ("", "SEM", "COM"):
            return after
    if "SEM ESPECIALIDADE" in u:
        return "Sem especialidade"
    return None


def _tokenize_items(blob):
    blob = re.sub(r'\s+', ' ', blob).strip()
    marks = []
    for m in ITEM_MARK.finditer(blob):
        if PRECEDE_BAD.search(blob[max(0, m.start() - 14):m.start()]):
            continue
        marks.append((m.start(), m.end(), m.group(1)))
    itens = []
    for i, (s, e, num) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(blob)
        texto = blob[e:end].strip(" .;–-")
        if texto:
            itens.append({"numero": num, "nivel": num.count(".") + 1, "texto": texto})
    return itens


def parse_markdown(text):
    meta, disciplinas, cur, started = {}, [], None, False
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        d = DISC_MD.match(line)
        if d:
            started = True
            cur = {"nome": d.group(2).strip(), "itens": []}
            disciplinas.append(cur)
            continue
        if not started:
            m = META.match(line)
            if m:
                k = META_MAP.get(m.group(1).strip().lower())
                if k:
                    meta[k] = m.group(2).strip()
                continue
            t = TITLE_H1.match(line)
            if t and "concurso" not in meta:
                meta["concurso"] = re.sub(r'\s*[—-]\s*Edital Verticalizado\s*$', '', t.group(1)).strip()
            continue
        a = ASSUNTO.match(line)
        if a and cur is not None:
            _add(cur, a.group(1), a.group(2)); continue
        n = NUMITEM.match(line)
        if n and cur is not None:
            _add(cur, n.group(1), n.group(2)); continue
    return meta, disciplinas, []   # md: cargo único (sem segmentação)


def parse_estruturado(text):
    """Editais reais: separa CONHECIMENTOS GERAIS (comuns) dos blocos por cargo."""
    lines = [s.strip() for s in text.splitlines() if s.strip() and not PAGE_NOISE.search(s.strip())]
    gerais, cargos = [], []
    mode, cur_list, cur_disc, buf, hdr = "pre", None, None, [], []

    def flush_disc():
        nonlocal buf
        if cur_disc is not None and buf:
            cur_disc["itens"] = _tokenize_items(" ".join(buf))
        buf = []

    def new_disc(name):
        nonlocal cur_disc
        flush_disc()
        cur_disc = {"nome": name, "itens": []}
        if cur_list is not None:
            cur_list.append(cur_disc)

    def start_cargo(name):
        nonlocal cur_list, cur_disc
        flush_disc(); cur_disc = None
        c = {"nome": name or f"Especialidade {len(cargos) + 1}", "disciplinas": []}
        cargos.append(c)
        cur_list = c["disciplinas"]

    for s in lines:
        U = _fold(s)
        if "CONHECIMENTOS GERAIS" in U:
            flush_disc(); cur_disc = None; cur_list = gerais; mode = "gerais"; hdr = []; continue
        if "CONHECIMENTOS ESPEC" in U:
            flush_disc(); cur_disc = None; cur_list = None; mode = "espec"; hdr = []; continue
        if mode == "espec" and ("ESPECIALIDADE" in U or U.startswith("CARGO") or _is_header_fragment(s)):
            hdr.append(s); continue
        if hdr and mode == "espec":
            start_cargo(_cargo_name(" ".join(hdr))); hdr = []
        if _is_caps_header(s) and not _is_section(s):
            new_disc(s.strip(" :–-")); continue
        if cur_disc is not None:
            buf.append(s)
    flush_disc()

    gerais = [d for d in gerais if d["itens"]]
    for c in cargos:
        c["disciplinas"] = [d for d in c["disciplinas"] if d["itens"]]
    cargos = [c for c in cargos if c["disciplinas"]]

    def _weak(n):
        f = _fold(n or "")
        if "SEM ESPECIALIDADE" in f:
            return False
        return (not n) or n.startswith("Especialidade ") or "ESPECIALIDADE" in f \
            or "GRUPO" in f or len(n) > 45 or any(ch.isdigit() for ch in n)
    for c in cargos:
        if _weak(c["nome"]) and c["disciplinas"]:
            c["nome"] = c["disciplinas"][0]["nome"]
        if c["nome"].isupper():
            c["nome"] = c["nome"].title()
    return gerais, cargos


def extract(path):
    suf = path.suffix.lower()
    if suf == ".md":
        meta, disciplinas, _ = parse_markdown(path.read_text(encoding="utf-8"))
        return meta, disciplinas, []          # gerais = todas; sem cargos
    if suf == ".pdf":
        import fitz
        full = "\n".join(p.get_text() for p in fitz.open(str(path)))
        up = full.upper()
        idx = up.find("CONTEÚDO PROGRAM")
        if idx == -1:
            idx = up.find("CONHECIMENTOS ESPEC")
        section = full[idx:] if idx != -1 else full
        m = re.search(r'\bANEXO\s+II\b', section.upper())
        if m and m.start() > 200:
            section = section[:m.start()]
        sys.stderr.write("[aviso] extração de PDF é heurística — confira o resumo.\n")
        gerais, cargos = parse_estruturado(section)
        return {}, gerais, cargos
    meta, g, c = {}, *parse_estruturado(path.read_text(encoding="utf-8", errors="ignore"))
    return meta, g, c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--out", "-o")
    ap.add_argument("--cargo", help="número (1..N) ou trecho do nome do cargo")
    ap.add_argument("--listar", action="store_true", help="só listar cargos detectados")
    for k in ("concurso", "orgao", "banca", "cargo_nome", "data_edital"):
        ap.add_argument(f"--{k}")
    args = ap.parse_args()

    p = Path(args.input)
    if not p.exists():
        sys.exit(f"ERRO: arquivo não encontrado: {p}")
    meta, gerais, cargos = extract(p)

    n_g = sum(len(d["itens"]) for d in gerais)
    if cargos:
        print(f"CONHECIMENTOS GERAIS (comuns): {len(gerais)} disciplinas, {n_g} itens")
        print(f"\nCARGOS / ESPECIALIDADES detectados ({len(cargos)}):")
        for i, c in enumerate(cargos, 1):
            ni = sum(len(d['itens']) for d in c['disciplinas'])
            print(f"  [{i}] {c['nome']}  —  {len(c['disciplinas'])} disc. específicas, {ni} itens")

    # selecionar cargo
    chosen = None
    if cargos and args.cargo:
        if args.cargo.isdigit() and 1 <= int(args.cargo) <= len(cargos):
            chosen = cargos[int(args.cargo) - 1]
        else:
            alvo = _fold(args.cargo)
            for c in cargos:
                if alvo in _fold(c["nome"]):
                    chosen = c; break
        if chosen is None:
            sys.exit(f"ERRO: cargo '{args.cargo}' não encontrado. Rode com --listar.")

    if args.listar or (cargos and not args.cargo):
        if cargos and not args.cargo and not args.listar:
            print("\n→ Reexecute com --cargo <nº|nome> --out edital.json para gerar a planilha desse cargo.")
        return

    disciplinas = list(gerais) + (chosen["disciplinas"] if chosen else [])
    data = {
        "concurso": args.concurso or meta.get("concurso", ""),
        "orgao": args.orgao or meta.get("orgao", ""),
        "banca": args.banca or meta.get("banca", ""),
        "cargo": args.cargo_nome or (chosen["nome"] if chosen else meta.get("cargo", "")),
        "data_edital": args.data_edital or meta.get("data_edital", ""),
        "disciplinas": disciplinas,
    }
    if not args.out:
        sys.exit("ERRO: informe --out para gravar o JSON.")
    Path(args.out).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tot = sum(len(d["itens"]) for d in disciplinas)
    print(f"\nOK -> {args.out}")
    print(f"Cargo: {data['cargo'] or '(único)'} | Disciplinas: {len(disciplinas)} | Itens: {tot}")


if __name__ == "__main__":
    main()
