#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera um PAINEL DE ESTUDO interativo (HTML único) a partir do JSON canônico.

Recursos: disciplinas recolhíveis, status por item (clique cicla A estudar →
Estudando → Estudado → Revisão), progresso por disciplina e global, busca e
filtro — tudo salvo no navegador (localStorage). Estética da marca (azul/slate, Sora).

Uso: python3 gerar_html.py edital.json --out painel.html
"""
import argparse, base64, json, os
from pathlib import Path

_LOGO_DEFAULT = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
LOGO = os.environ.get("EDITAL_LOGO") or str(_LOGO_DEFAULT)  # opcional: marca própria do usuário


def build(data, out):
    try:
        logo = "data:image/png;base64," + base64.b64encode(Path(LOGO).read_bytes()).decode()
    except Exception:
        logo = ""
    payload = json.dumps({
        "concurso": data.get("concurso", ""), "cargo": data.get("cargo", ""),
        "orgao": data.get("orgao", ""), "disciplinas": data.get("disciplinas", []),
    }, ensure_ascii=False)

    html = """<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Edital Verticalizado — Painel de Estudo</title>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root{--azul:#2563EB;--azul2:#3B82F6;--slate:#0f172a;--slate2:#1e293b;--bg:#f1f5f9;--card:#fff;
--txt:#1e293b;--mut:#64748b;--bd:#e2e8f0;--verde:#16a34a;--amar:#d97706;--verm:#dc2626;}
*{margin:0;box-sizing:border-box}
body{font-family:'Sora',sans-serif;background:var(--bg);color:var(--txt);font-size:15px}
header{position:sticky;top:0;z-index:10;background:linear-gradient(135deg,#0f172a,#1e293b);color:#fff;
padding:14px 22px;box-shadow:0 4px 20px rgba(0,0,0,.25)}
.top{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.logo{width:42px;height:42px;border-radius:11px;background:rgba(255,255,255,.07);
border:1px solid rgba(255,255,255,.12);display:flex;align-items:center;justify-content:center}
.logo img{width:30px}
h1{font-size:18px;font-weight:700}.sub{font-size:13px;color:#94a3b8}
.gstat{margin-left:auto;text-align:right}
.gstat b{font-size:26px;font-weight:800;background:linear-gradient(135deg,#60a5fa,#3b82f6);
-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.gbar{height:7px;border-radius:6px;background:rgba(255,255,255,.12);margin-top:10px;overflow:hidden}
.gbar>span{display:block;height:100%;background:linear-gradient(90deg,#2563EB,#60a5fa);width:0;transition:width .3s}
.tools{display:flex;gap:10px;margin-top:12px;flex-wrap:wrap}
.tools input,.tools select{font-family:inherit;font-size:13px;padding:8px 12px;border-radius:10px;
border:1px solid rgba(255,255,255,.15);background:rgba(255,255,255,.08);color:#fff}
.tools input{flex:1;min-width:160px}.tools input::placeholder{color:#94a3b8}
.tools select option{color:#000}
.btn{font-family:inherit;font-size:13px;padding:8px 12px;border-radius:10px;border:1px solid rgba(255,255,255,.15);background:rgba(255,255,255,.08);color:#fff;cursor:pointer}
.btn:hover{background:rgba(255,255,255,.16)}
main{max-width:1000px;margin:22px auto;padding:0 16px}
.disc{background:var(--card);border:1px solid var(--bd);border-radius:14px;margin-bottom:14px;overflow:hidden;
box-shadow:0 1px 3px rgba(15,23,42,.04)}
.dh{display:flex;align-items:center;gap:12px;padding:14px 18px;cursor:pointer;user-select:none}
.dh:hover{background:#f8fafc}
.dh .nm{font-weight:600;font-size:15px;flex:1}
.dh .pc{font-size:13px;font-weight:600;color:var(--azul);min-width:42px;text-align:right}
.dh .ct{font-size:12px;color:var(--mut)}
.dbar{height:6px;width:120px;border-radius:5px;background:#eef2f7;overflow:hidden}
.dbar>span{display:block;height:100%;background:linear-gradient(90deg,#2563EB,#60a5fa);width:0}
.chev{transition:transform .2s;color:var(--mut)}
.disc.collapsed .items{display:none}.disc.collapsed .chev{transform:rotate(-90deg)}
.items{border-top:1px solid var(--bd)}
.it{display:flex;align-items:flex-start;gap:12px;padding:9px 18px;border-bottom:1px solid #f1f5f9}
.it:last-child{border-bottom:0}
.it .st{flex:0 0 auto;width:22px;height:22px;border-radius:7px;border:2px solid #cbd5e1;cursor:pointer;
margin-top:1px;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:800;color:#fff}
.it[data-s="estudando"] .st{background:var(--amar);border-color:var(--amar)}
.it[data-s="estudado"] .st{background:var(--verde);border-color:var(--verde)}
.it[data-s="revisao"] .st{background:var(--azul);border-color:var(--azul)}
.it .num{flex:0 0 auto;color:var(--mut);font-variant-numeric:tabular-nums;font-size:13px;min-width:34px}
.it .tx{flex:1}
.it[data-s="estudado"] .tx,.it[data-s="revisao"] .tx{color:var(--mut)}
.it.n1 .tx{font-weight:600}.it.n2 .tx{padding-left:18px}.it.n3 .tx{padding-left:36px;font-size:14px}
.it.hide{display:none}
.foot{text-align:center;color:var(--mut);font-size:12px;margin:24px 0}
.leg{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--mut);margin-top:10px}
.leg i{width:12px;height:12px;border-radius:4px;display:inline-block;margin-right:5px;vertical-align:-1px}
@media print{header{position:static}.tools,.chev{display:none}.disc.collapsed .items{display:block}}
</style></head><body>
<header>
  <div class="top">
    <div class="logo">__LOGO__</div>
    <div><h1>Edital Verticalizado</h1><div class="sub" id="sub"></div></div>
    <div class="gstat"><b id="gpc">0%</b><div class="sub" id="gct"></div></div>
  </div>
  <div class="gbar"><span id="gbar"></span></div>
  <div class="tools">
    <input id="q" placeholder="🔎 Buscar assunto...">
    <select id="fs">
      <option value="">Todos os status</option>
      <option value="pend">Pendentes (não concluídos)</option>
      <option value="">— </option>
      <option value="">A estudar</option>
      <option value="estudando">Estudando</option>
      <option value="estudado">Estudado</option>
      <option value="revisao">Revisão</option>
    </select>
    <button id="exp" class="btn">Recolher/expandir</button>
    <button id="save" class="btn" title="Baixar um arquivo com seu progresso">💾 Salvar progresso</button>
    <button id="load" class="btn" title="Carregar um arquivo de progresso salvo">📂 Carregar</button>
    <input id="file" type="file" accept="application/json,.json" style="display:none">
  </div>
  <div class="leg"><span><i style="background:#cbd5e1"></i>A estudar</span><span><i style="background:#d97706"></i>Estudando</span><span><i style="background:#16a34a"></i>Estudado</span><span><i style="background:#2563EB"></i>Revisão</span></div>
</header>
<main id="app"></main>
<div class="foot">Seu progresso fica salvo automaticamente neste navegador.</div>
<script>
const DATA = __DATA__;
const ORDER = ["", "estudando", "estudado", "revisao"];
const MARK = {"":"","estudando":"~","estudado":"✓","revisao":"R"};
const slug = (DATA.concurso+"|"+DATA.cargo).replace(/\\s+/g,"_").slice(0,80);
const KEY = "vep:"+slug;
let state = {};
try{ state = JSON.parse(localStorage.getItem(KEY)||"{}"); }catch(e){ state = {}; }
const done = s => s==="estudado"||s==="revisao";
function save(){ localStorage.setItem(KEY, JSON.stringify(state)); }

document.getElementById("sub").textContent = [DATA.concurso, DATA.cargo].filter(Boolean).join(" · ");

const app = document.getElementById("app");
DATA.disciplinas.forEach((d,di)=>{
  const sec=document.createElement("section"); sec.className="disc"; sec.dataset.di=di;
  let its="";
  d.itens.forEach(it=>{
    const id="d"+di+"-"+it.numero; const s=state[id]||"";
    its+=`<div class="it n${it.nivel}" data-id="${id}" data-s="${s}" data-tx="${(it.texto||'').toLowerCase()}">
      <div class="st" title="Clique para mudar o status">${MARK[s]}</div>
      <div class="num">${it.numero}</div><div class="tx">${it.texto||""}</div></div>`;
  });
  sec.innerHTML=`<div class="dh"><i class="chev">▾</i><span class="nm">${d.nome}</span>
    <span class="ct">${d.itens.length} itens</span>
    <div class="dbar"><span></span></div><span class="pc">0%</span></div>
    <div class="items">${its}</div>`;
  app.appendChild(sec);
});

function pct(di){ const sec=app.querySelector(`.disc[data-di="${di}"]`);
  const its=[...sec.querySelectorAll(".it")]; const c=its.filter(x=>done(x.dataset.s)).length;
  const p=its.length?Math.round(100*c/its.length):0;
  sec.querySelector(".pc").textContent=p+"%"; sec.querySelector(".dbar>span").style.width=p+"%"; return [c,its.length];
}
function refresh(){ let tot=0,cc=0;
  DATA.disciplinas.forEach((d,di)=>{const [c,n]=pct(di);tot+=n;cc+=c;});
  const p=tot?Math.round(100*cc/tot):0;
  document.getElementById("gpc").textContent=p+"%";
  document.getElementById("gbar").style.width=p+"%";
  document.getElementById("gct").textContent=cc+" de "+tot+" itens";
}
app.addEventListener("click",e=>{
  const st=e.target.closest(".st");
  if(st){ const it=st.closest(".it"); const cur=it.dataset.s||"";
    const nx=ORDER[(ORDER.indexOf(cur)+1)%ORDER.length]; it.dataset.s=nx;
    st.textContent=MARK[nx]; if(nx){state[it.dataset.id]=nx;}else{delete state[it.dataset.id];}
    save(); refresh(); return; }
  const dh=e.target.closest(".dh"); if(dh){ dh.closest(".disc").classList.toggle("collapsed"); }
});
document.getElementById("exp").onclick=()=>{
  const any=app.querySelector(".disc:not(.collapsed)");
  app.querySelectorAll(".disc").forEach(s=>s.classList.toggle("collapsed", !!any));
};
function applyFilter(){ const q=document.getElementById("q").value.toLowerCase().trim();
  const fs=document.getElementById("fs").value;
  app.querySelectorAll(".disc").forEach(sec=>{ let vis=0;
    sec.querySelectorAll(".it").forEach(it=>{
      let ok=true; if(q && !it.dataset.tx.includes(q)) ok=false;
      if(fs==="pend" && done(it.dataset.s)) ok=false;
      else if(fs && fs!=="pend" && (it.dataset.s||"")!==fs) ok=false;
      it.classList.toggle("hide",!ok); if(ok)vis++; });
    sec.style.display=vis?"":"none"; });
}
document.getElementById("q").addEventListener("input",applyFilter);
document.getElementById("fs").addEventListener("change",applyFilter);

// --- salvar / carregar progresso (export/import .json) ---
function exportProgress(){
  const payload={app:"verticalizar-edital-pro",concurso:DATA.concurso,cargo:DATA.cargo,exportadoEm:new Date().toISOString(),state};
  const blob=new Blob([JSON.stringify(payload,null,2)],{type:"application/json"});
  const a=document.createElement("a"); a.href=URL.createObjectURL(blob);
  a.download="progresso-"+(slug||"edital")+".json"; document.body.appendChild(a); a.click();
  a.remove(); URL.revokeObjectURL(a.href);
}
function importProgress(file){
  const rd=new FileReader();
  rd.onload=ev=>{ try{ const j=JSON.parse(ev.target.result); const st=(j&&j.state)?j.state:j;
    if(typeof st!=="object"||!st) throw 0;
    if(j&&j.cargo&&DATA.cargo&&j.cargo!==DATA.cargo&&!confirm("Este progresso é de outro cargo (\\""+j.cargo+"\\"). Carregar mesmo assim?")) return;
    state=st; save();
    app.querySelectorAll(".it").forEach(it=>{ const s=state[it.dataset.id]||""; it.dataset.s=s; it.querySelector(".st").textContent=MARK[s]; });
    refresh(); alert("Progresso carregado com sucesso.");
  }catch(e){ alert("Arquivo de progresso inválido."); } };
  rd.readAsText(file);
}
document.getElementById("save").onclick=exportProgress;
document.getElementById("load").onclick=()=>document.getElementById("file").click();
document.getElementById("file").addEventListener("change",e=>{ if(e.target.files[0])importProgress(e.target.files[0]); e.target.value=""; });
refresh();
</script></body></html>"""
    html = html.replace("__LOGO__", f'<img src="{logo}">' if logo else "📋").replace("__DATA__", payload)
    Path(out).write_text(html, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json"); ap.add_argument("--out", "-o", required=True)
    a = ap.parse_args()
    data = json.loads(Path(a.json).read_text(encoding="utf-8"))
    build(data, a.out)
    n = sum(len(d["itens"]) for d in data.get("disciplinas", []))
    print(f"OK -> {a.out} | {len(data.get('disciplinas', []))} disciplinas, {n} itens")


if __name__ == "__main__":
    main()
