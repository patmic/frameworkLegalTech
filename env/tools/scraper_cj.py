#!/usr/bin/env python3
"""
scraper_cj.py — Instrumento de recolección documental reproducible (Protocolo v1)
==================================================================================
Captura snapshots verificables de las fuentes oficiales del Consejo de la
Judicatura del Ecuador definidas en env/data/evidence/sources_semilla.json.

Cada corrida produce:
  env/data/evidence/<run_id>/<slug>.html     — snapshot de la fuente
  env/data/evidence/<run_id>/manifest.json   — URL, timestamp, bytes, SHA-256 por fuente
y registra la corrida en env/data/bitacora.json (append-only, hash-encadenada).

Reproducibilidad: otro investigador con este script + sources_semilla.json +
la fecha de corte puede repetir la captura y comparar hashes.

Uso:
  python env/tools/scraper_cj.py                          # corrida con fecha de hoy
  python env/tools/scraper_cj.py --fecha-corte 2026-07-02 # etiqueta la corrida
  python env/tools/scraper_cj.py --data-dir ./env/data    # raíz de datos (default ./env/data)
  python env/tools/scraper_cj.py --verificar <run_id>     # re-hash de una corrida
Solo stdlib — sin dependencias.
"""
import argparse, hashlib, json, ssl, sys, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path

UA = "MALTG-SDT-Auditor/1.0 (+legaltech-governance-scraper; protocolo v1)"

DEFAULT_SEEDS = [
    {"slug":"portal_cj","label":"Portal CJ","url":"https://www.funcionjudicial.gob.ec/","dimensiones":["D2"],"incluida":True,"criterio":"Fuente oficial (*.funcionjudicial.gob.ec)"},
    {"slug":"satje_spa","label":"SATJE Consulta de Procesos (SPA v4.0.1)","url":"https://procesosjudiciales.funcionjudicial.gob.ec/busqueda","dimensiones":["D2"],"incluida":True,"criterio":"Fuente oficial"},
    {"slug":"esatje_ogje","label":"e-SATJE 2020 (OGJE)","url":"https://www.funcionjudicial.gob.ec/satje/","dimensiones":["D2"],"incluida":True,"criterio":"Fuente oficial"},
    {"slug":"plan_estrategico_2026_2031","label":"Plan Estrategico 2026-2031","url":"https://www.funcionjudicial.gob.ec/el-pleno-aprueba-el-plan-estrategico-2026-2031-para-transformar-la-funcion-judicial/","dimensiones":["D3"],"incluida":True,"criterio":"Fuente oficial"},
    {"slug":"inversion_transf_digital","label":"Inversion en transformacion digital / infra obsoleta","url":"https://www.funcionjudicial.gob.ec/consejo-de-la-judicatura-prioriza-inversion-en-la-transformacion-digital-repotenciacion-de-la-infraestructura-y-combate-a-la-impunidad/","dimensiones":["D3"],"incluida":True,"criterio":"Fuente oficial"},
    {"slug":"iso37001_sgas","label":"ISO 37001 Antisoborno (SGAS)","url":"https://www.funcionjudicial.gob.ec/sistema-de-gestion-antisoborno-de-acuerdo-a-la-norma-iso-37001/","dimensiones":["D4"],"incluida":True,"criterio":"Fuente oficial"},
    {"slug":"modernizacion_disciplinario","label":"Modernizacion del sistema disciplinario","url":"https://www.funcionjudicial.gob.ec/consejo-de-la-judicatura-modernizara-su-sistema-disciplinario-con-plataforma-de-ultima-generacion-y-controles-de-seguridad/","dimensiones":["D4"],"incluida":True,"criterio":"Fuente oficial"},
    {"slug":"plan_integridad_2024_2028","label":"Plan Nacional de Integridad Publica 2024-2028","url":"https://www.funcionjudicial.gob.ec/consejo-de-la-judicatura-se-adhiere-al-plan-nacional-de-integridad-publica-y-lucha-contra-la-corrupcion-2024-2028/","dimensiones":["D4"],"incluida":True,"criterio":"Fuente oficial"},
    {"slug":"justicia_abierta","label":"Justicia Abierta — datos abiertos judiciales","url":"https://www.funcionjudicial.gob.ec/consejo-de-la-judicatura-trabaja-en-el-portal-unico-de-datos-abiertos-y-estadistica-judicial-justicia-abierta-transparentando-la-informacion-para-combatir-la-corrupcion/","dimensiones":["D1"],"incluida":True,"criterio":"Fuente oficial"},
    {"slug":"ckan_datosabiertos_cj","label":"Datos Abiertos Ecuador (CKAN) — organizacion CJ","url":"https://datosabiertos.gob.ec/dataset/?organization=cj","dimensiones":["D1"],"incluida":True,"criterio":"Fuente oficial (*.gob.ec)"},
    {"slug":"portal_estadisticas","label":"Portal de Estadisticas Judiciales","url":"https://fsweb.funcionjudicial.gob.ec/estadisticas/datoscj/portalestadistica.html","dimensiones":["D1"],"incluida":True,"criterio":"Fuente oficial"},
]

def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def http_get(url, timeout=12):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        raw = r.read(400_000)
        enc = r.headers.get_content_charset() or "utf-8"
        return r.status, raw.decode(enc, "replace")

def load_seeds(ev_dir: Path):
    seed_path = ev_dir / "sources_semilla.json"
    if seed_path.exists():
        return json.loads(seed_path.read_text(encoding="utf-8"))
    ev_dir.mkdir(parents=True, exist_ok=True)
    seed_path.write_text(json.dumps(DEFAULT_SEEDS, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[i] Semillas creadas: {seed_path}")
    return DEFAULT_SEEDS

def bitacora_log(data_dir: Path, actor, accion, detalle, refs):
    path = data_dir / "bitacora.json"
    entries = []
    if path.exists():
        try: entries = json.loads(path.read_text(encoding="utf-8"))
        except Exception: entries = []
    prev = entries[-1]["hash"] if entries else "GENESIS"
    e = {"id": len(entries) + 1, "ts": now_iso(), "tipo": "sistema",
         "actor": actor, "accion": accion, "detalle": detalle, "refs": refs, "prev_hash": prev}
    e["hash"] = hashlib.sha256(json.dumps(e, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]
    entries.append(e)
    path.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")

def capturar(data_dir: Path, fecha_corte: str):
    ev_dir = data_dir / "evidence"
    seeds = load_seeds(ev_dir)
    stamp = datetime.now(timezone.utc)
    run_id = (fecha_corte or stamp.strftime("%Y-%m-%d")) + "_" + stamp.strftime("%H%M%S")
    n = 1
    while (ev_dir / run_id).exists():
        n += 1
        run_id = run_id.split("-v")[0] + f"-v{n}"
    run_dir = ev_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for s in seeds:
        if not s.get("incluida", True):
            print(f"  – {s['slug']}: EXCLUIDA ({s.get('criterio','')})")
            entries.append({"slug": s["slug"], "url": s["url"], "ok": False, "excluida": True})
            continue
        t0 = time.time()
        try:
            status, html = http_get(s["url"])
            (run_dir / (s["slug"] + ".html")).write_text(html, encoding="utf-8")
            sha = hashlib.sha256(html.encode("utf-8")).hexdigest()
            entries.append({"slug": s["slug"], "label": s["label"], "url": s["url"],
                            "ok": 200 <= status < 400, "status": status,
                            "bytes": len(html.encode("utf-8")), "sha256": sha,
                            "file": f"{run_id}/{s['slug']}.html",
                            "ms": int((time.time() - t0) * 1000), "captured_at": now_iso(),
                            "dimensiones": s.get("dimensiones", [])})
            print(f"  ✓ {s['slug']}: HTTP {status} · {len(html)} chars · sha256 {sha[:16]}…")
        except Exception as e:
            entries.append({"slug": s["slug"], "label": s.get("label",""), "url": s["url"],
                            "ok": False, "error": str(e)[:160]})
            print(f"  ✗ {s['slug']}: {e}")
    n_ok = sum(1 for e in entries if e.get("ok"))
    manifest = {"run_id": run_id, "captured_at": now_iso(), "user_agent": UA,
                "seed_file": "sources_semilla.json", "protocol": "PROTOCOLO.md",
                "n_total": len(entries), "n_ok": n_ok, "entries": entries}
    (run_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    bitacora_log(data_dir, "investigador/scraper_cj.py", "captura_evidencia",
                 f"Corrida {run_id}: {n_ok}/{len(entries)} fuentes capturadas.", [run_id])
    print(f"\n[✓] Manifest: {run_dir / 'manifest.json'}  ({n_ok}/{len(entries)} OK)")
    return 0 if n_ok else 1

def verificar(data_dir: Path, run_id: str):
    run_dir = data_dir / "evidence" / run_id
    mf = run_dir / "manifest.json"
    if not mf.exists():
        print(f"[✗] No existe {mf}"); return 1
    m = json.loads(mf.read_text(encoding="utf-8"))
    ok_all = True
    for e in m.get("entries", []):
        if not e.get("ok"): continue
        f = data_dir / "evidence" / e["file"]
        if not f.exists():
            print(f"  ✗ {e['slug']}: FALTANTE"); ok_all = False; continue
        sha = hashlib.sha256(f.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
        estado = "INTEGRO" if sha == e["sha256"] else "ALTERADO"
        ok_all = ok_all and (estado == "INTEGRO")
        print(f"  {'✓' if estado=='INTEGRO' else '✗'} {e['slug']}: {estado}")
    print(f"\n[{'✓' if ok_all else '✗'}] Evidencia {'INTEGRA' if ok_all else 'COMPROMETIDA'} — corrida {run_id}")
    return 0 if ok_all else 1

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Captura reproducible de evidencia del ecosistema CJ")
    ap.add_argument("--data-dir", default="./env/data", help="Raíz de datos (default ./env/data)")
    ap.add_argument("--fecha-corte", default="", help="Etiqueta YYYY-MM-DD de la corrida")
    ap.add_argument("--verificar", default="", metavar="RUN_ID", help="Verificar hashes de una corrida existente")
    a = ap.parse_args()
    d = Path(a.data_dir)
    sys.exit(verificar(d, a.verificar) if a.verificar else capturar(d, a.fecha_corte))
