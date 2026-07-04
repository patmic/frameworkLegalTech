# Protocolo de Recolección Documental — Evidencia SDT_CJ (v1)
**Proyecto:** MALTG LegalTech Validator · **Fecha de vigencia:** 2026-07-02
**Instrumento:** análisis documental sistemático de fuentes oficiales mediante web scraping con snapshots verificables.

## 1. Objetivo
Recolectar de forma **reproducible y verificable** la evidencia pública que sustenta el
Modelo Digital Estructural del Consejo de la Judicatura (`/data/sdt/SDT_CJ.json`) y los
scores de sus dimensiones de madurez (D1–D4). Este protocolo corrige el fallo
metodológico "scraping sin protocolo" (ver `ANALISIS_CONCEPTUAL.md` y `PLAN_CORRECCION_FALLOS.md`).

## 2. Criterios de inclusión
1. Fuentes **oficiales** únicamente: dominios `*.funcionjudicial.gob.ec` y portales estatales `*.gob.ec` (ej. datosabiertos.gob.ec).
2. Contenido **público**, accesible sin autenticación.
3. Pertinencia directa a una dimensión de madurez (D1 datos/semántica, D2 arquitectura/integración, D3 estrategia, D4 compliance).
4. Documentos institucionales con valor probatorio: planes aprobados, resoluciones, comunicados del Pleno, portales de servicio en producción.

## 3. Criterios de exclusión
1. Prensa, blogs, redes sociales y fuentes de terceros no estatales.
2. Contenido tras autenticación o datos personales (solo metadatos/estructura pública).
3. Páginas duplicadas o espejos no canónicos.

## 4. Fuentes semilla
Registradas en `sources_semilla.json` (slug, etiqueta, URL, dimensiones que sustenta,
bandera `incluida`, criterio). **Toda alta/baja de fuente se registra en la bitácora.**

## 5. Procedimiento de captura (fases)
1. **Identificación:** revisión de las fuentes semilla vigentes.
2. **Captura:** descarga de cada fuente con user-agent declarado
   (`MALTG-SDT-Auditor/1.0 (+legaltech-governance-scraper; protocolo v1)`),
   límite 400 KB por página, timeout 10–12 s. Snapshot HTML guardado en
   `evidence/<run_id>/<slug>.html`; `run_id = <fecha-corte>_<HHMMSS>` UTC.
3. **Verificación de integridad:** `manifest.json` por corrida con URL, timestamp UTC,
   bytes y **SHA-256** de cada snapshot. La verificación re-hashea los archivos y
   compara contra el manifest (`/api/evidence/verify` o `env/tools/scraper_cj.py --verificar`).
4. **Codificación:** los hallazgos se mapean a componentes y dimensiones del SDT_CJ;
   cada fuente lleva `slug` que enlaza el snapshot (trazabilidad campo→fuente).

## 6. Ejecución
- **En la app:** tab *Bitácora · Evidencia* → «Capturar evidencia», o botón «scraping CJ» del tab SDT_CJ (captura + regeneración del SDT).
- **Fuera de la app (reproducción independiente):** `python env/tools/scraper_cj.py --fecha-corte YYYY-MM-DD`.

## 7. Registro (bitácora)
Toda corrida, verificación y decisión metodológica queda en `/data/bitacora.json`:
registro **append-only encadenado por hash** (mismo principio que el ledger del expediente),
consultable en el tab *Bitácora · Evidencia*. Las entradas manuales identifican al investigador.

## 8. Reproducibilidad
Un tercero con este repositorio puede: (a) repetir la captura en una nueva fecha de corte y
comparar cambios; (b) verificar que los snapshots citados no fueron alterados desde su captura
(SHA-256); (c) auditar la cronología completa de decisiones en la bitácora.

## 9. Limitaciones declaradas
- El snapshot captura el HTML servido (400 KB máx.); no ejecuta JavaScript, por lo que las SPA
  (ej. SATJE v4) se documentan por su shell + señales técnicas, no por su contenido dinámico.
- La web es mutable: los hashes prueban integridad del snapshot, no permanencia de la fuente.
- La verificación TLS está relajada (certificados estatales inconsistentes); se registra el riesgo.
