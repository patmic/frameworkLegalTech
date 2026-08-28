# Plan de Corrección — Fallos Conceptuales Vigentes (MALTG v3)
**Fecha:** 2026-07-02 · **Complementa:** `ANALISIS_CONCEPTUAL.md`

Cada fallo tiene pasos concretos referidos a los artefactos reales del proyecto (`backend/main.py`, `env/data/sdt/SDT_CJ.json`, `env/data/cogep_kb.json`, `/data/LegalCase`).

---

## Fallo 1 — Circularidad de la validación (evidencia no independiente)

**Meta:** que ningún score del radar sea una etiqueta declarada por el autor sin respaldo verificable.

1. **Rúbrica por dimensión.** Redacta para cada una de las 9 dimensiones una rúbrica 0–10 con criterios observables por nivel (ej. INTEROP nivel 6 = "expone API pública documentada"). Guárdala como `env/data/rubrica_dimensiones.json`.
2. **Campo de evidencia.** Añade a cada dimensión de `SDT_CJ.json` un arreglo `evidence[]`: `{url, fecha_acceso, tipo, extracto, criterio_rubrica}`. Un score sin evidencia asociada queda marcado "declarado" en la UI.
3. **Índice empírico procesal.** Crea endpoint `GET /api/cogep/salud-global` que ejecute `razonar_expediente()` en lote sobre todo `/data/LegalCase` y devuelva: índice global 0–100 (actos en plazo / evaluables), desglose por procedimiento y por causa.
4. **Cerrar el ciclo.** Modifica `compute_validation()` para que el score de la dimensión Operational (y el componente procesal de LegalTech) se calcule desde ese índice empírico, no desde el valor declarado. Documenta la función de mapeo (ej. score = índice/10).
5. **Doble evaluador.** Pide a un segundo experto puntuar las dimensiones restantes con la rúbrica y las evidencias. Calcula concordancia (kappa de Cohen o correlación de Spearman) y repórtala en la tesis.
6. **Redacción.** En metodología: "los scores provienen de (a) evidencia documental pública con rúbrica y doble evaluador, y (b) medición empírica sobre expedientes reales" — la circularidad desaparece del argumento.

**Criterio de éxito:** cada score del radar es trazable a una URL/expediente o a una rúbrica aplicada por ≥2 evaluadores.

---

## Fallo 2 — Scraping sin protocolo reproducible

**Meta:** convertir "web scraping" en un instrumento de recolección documental defendible.

1. **Script reproducible.** Crea `env/tools/scraper_cj.py` con la lista de URLs semilla (las 8+ ya citadas en `sources` de SDT_CJ), user-agent declarado y fecha de corte como parámetro.
2. **Snapshots con hash.** Guarda cada página en `env/data/evidence/YYYY-MM-DD/<slug>.html` + un `manifest.json` con URL, timestamp y SHA-256. Eso congela la evidencia (las webs del CJ cambian).
3. **Criterios de inclusión/exclusión.** Documenta por escrito: solo fuentes oficiales (*.funcionjudicial.gob.ec, registros oficiales), periodo cubierto, qué se descarta (prensa, blogs).
4. **Trazabilidad campo→fuente.** Regenera `SDT_CJ.json` de modo que cada servicio/capa cite el snapshot del que proviene (`source_ref`).
5. **Capítulo metodología.** Describe el protocolo como "análisis documental sistemático de fuentes oficiales" con las fases: identificación → captura → verificación de integridad → codificación contra rúbrica.

**Criterio de éxito:** otro investigador puede re-ejecutar el scraper en la fecha de corte y reconstruir SDT_CJ.

---

## Fallo 3 — Métrica Ψ con pesos arbitrarios e INTEROP inconsistente

**Meta:** pesos justificados y modelo formal homogéneo.

1. **Formaliza el estado actual.** Escribe la definición exacta de Ψ(d)=0.4·root+0.6·subs y la fórmula INTEROP tal como está en `psi()` y `compute_validation()` — es la línea base a justificar o corregir.
2. **Panel de expertos (AHP).** Recluta 3–7 expertos (gobernanza TI / derecho procesal). Cada uno llena matrices de comparación por pares: (a) importancia root vs. subs, (b) importancia relativa de las 9 dimensiones. Calcula pesos con eigenvector y verifica razón de consistencia CR < 0.10. Alternativa con menos acceso: Delphi de 2 rondas con cuestionario Likert y mediana como peso.
3. **Homogeneiza INTEROP.** Reescríbela como caso particular de la fórmula general: subdimensiones {OpenData, Security, CrossLinks} con pesos propios y sin reutilizar los `dt_refs` que ya puntúan en otras dimensiones (elimina el doble conteo). Un solo Ψ para las 9 dimensiones.
4. **Análisis de sensibilidad.** Script `env/tools/sensibilidad.py`: perturba cada peso ±10 % y ±20 %, recalcula el score global y el nivel de madurez de SDT_CJ. Reporta si el nivel (46 → "Definido") es estable. Gráfico tornado para la tesis.
5. **Actualiza el código.** `psi()` lee los pesos desde `env/data/pesos_ahp.json` (no hard-coded) y el endpoint `/api/methodology` documenta su origen.

**Criterio de éxito:** cada peso tiene procedencia (AHP/Delphi + CR) y el resultado es robusto ante ±10 %.

---

## Fallo 4 — Terminología imprecisa de "gemelo digital"

**Meta:** consistencia total entre tesis, UI y datos usando la taxonomía aceptada.

1. **Glosario formal.** Sección de tesis con las definiciones de Kritzinger et al. (2018): *digital model* (sin flujo automático), *digital shadow* (flujo real→digital), *digital twin* (bidireccional); añade *cognitive digital twin* (Zheng et al.) para la parte de razonamiento.
2. **Clasifica cada artefacto.** Tabla: SDT_CJ = **modelo digital estructural** (snapshot, sin telemetría); expedientes SATJE + razonador COGEP = **sombra digital cognitiva** (datos reales → representación → dictamen, sin retroalimentación al sistema).
3. **Renombra en la app.** En `frontend/index.html` y en los `meta.title` de los JSON: "Gemelo Digital Estructural" → "Modelo Digital Estructural (SDT)"; el tab del razonador → "Sombra Digital Cognitiva". O conserva "gemelo" como nombre comercial pero con nota visible de clasificación taxonómica.
4. **Ruta a gemelo pleno (trabajo futuro).** Diseña conceptualmente la retroalimentación que lo convertiría en twin: alertas de plazo → notificación/oficio al sistema real (e-SATJE). No lo implementes; decláralo como condición formal pendiente. Esto muestra dominio de la taxonomía en vez de esconder la limitación.

**Criterio de éxito:** ningún revisor puede señalar discrepancia entre lo que el texto llama gemelo y lo que el artefacto es.

---

## Fallo 5 — Razonador sin validez medida

**Meta:** métricas de desempeño contra un estándar anotado por experto humano.

1. **Gold standard.** Selecciona 30–50 actuaciones de los expedientes de `/data/LegalCase` (estratifica: ordinario/sumario/ejecución). Un abogado anota por cada una: acto procesal correcto, fechas relevantes y veredicto correcto (CUMPLE/ALERTA/INCUMPLE). Formato `env/data/gold/gold_standard.json` + guía de anotación de 1 página.
2. **Script de evaluación.** `env/tools/eval_razonador.py`: corre `_match_acto()` y `razonar_expediente()` sobre el gold standard y calcula precision/recall/F1 del mapeo providencia→acto y exactitud del veredicto, con matriz de confusión.
3. **Feriados y suspensiones.** Crea `env/data/feriados_judiciales.json` (feriados nacionales + suspensiones de término del Consejo de la Judicatura por año) y modifica `business_days()` para excluirlos. Es la mayor fuente de falsos INCUMPLE.
4. **Itera.** Analiza los errores del mapeo léxico; amplía keywords o añade desempate por posición en la etapa procesal. Re-evalúa y reporta línea base vs. mejorado.
5. **Segundo anotador (deseable).** 15–20 actuaciones anotadas por un segundo abogado → kappa inter-anotador; valida que la tarea misma es objetiva.
6. **Reporta.** Tabla de métricas + matriz de confusión + análisis de errores en el capítulo de resultados. Declara el umbral aceptado (ej. F1 ≥ 0.85 para uso como indicador agregado).

**Criterio de éxito:** el "dictamen IA" deja de ser demostración y pasa a sistema evaluado con desempeño conocido.

---

## Fallo 6 — Muestra de expedientes sin diseño muestral

**Meta:** justificar qué representan las ~50 causas y qué conclusiones permiten.

1. **Define la población.** Ej.: "causas tramitadas bajo COGEP (procedimientos ordinario, sumario y ejecución) en unidades judiciales civiles del Ecuador, 2022–2024, consultables en el portal público SATJE".
2. **Declara el tipo de muestreo.** Lo que tienes es **muestreo intencional (no probabilístico) estratificado** por procedimiento y provincia. Nómbralo así; no pretendas aleatoriedad.
3. **Tabla de caracterización.** Script `env/tools/caracterizar_muestra.py` que genere del contenido de `/data/LegalCase`: N por procedimiento, provincia (dígitos 1–2 del número de causa), año, materia y estado. Inclúyela en la tesis.
4. **Alcance de las conclusiones.** Redacta: el estudio permite *generalización analítica* (el método funciona y detecta incumplimientos) mas no inferencia estadística poblacional. Si el índice agregado alimenta el radar (Fallo 1), preséntalo como "indicador sobre la muestra estudiada".
5. **Ampliación opcional.** Si el tiempo lo permite, amplía a N≥100 con descarga sistemática del portal (ej. todas las causas de un juzgado en un rango de fechas) — eso sí habilita estadística descriptiva sólida por estrato.

**Criterio de éxito:** la tesis declara población, tipo de muestreo, caracterización y límites de generalización sin sobre-reclamar.

---

## Fallo 7 — Ontologías no evaluadas como ontologías

**Meta:** que MALTG y COGEP resistan escrutinio de ingeniería ontológica.

1. **Unifica IRIs y versiones.** Un solo namespace (`http://maltg.arch/onto#` en OWL, JSON-LD y código) y una sola versión (docker-compose, API, `versionInfo`). Es mecánico pero elimina la incoherencia formal.
2. **COGEP a OWL.** Script `env/tools/kb2owl.py` (owlready2) que convierta `cogep_kb.json` en `COGEP_ontology.owl`: clases Procedimiento/Etapa/ActoProcesal/Término/Sujeto, object properties (tieneEtapa, contieneActo, sujetoATermino, computaDesde), individuos con anotación del artículo. La KB JSON queda como formato de edición; el OWL como formalización.
3. **Alinea a una ontología legal de referencia.** Declara equivalencias/subsunciones con LKIF-Core (acto jurídico, norma, agente) y expresa las reglas de plazo en sintaxis LegalRuleML o SWRL en un anexo. No hace falta re-implementar el razonador: basta demostrar que las reglas son expresables en el estándar.
4. **Verificación lógica.** Corre HermiT o Pellet sobre ambas ontologías: consistencia, ausencia de clases insatisfacibles. Adjunta el reporte.
5. **OOPS! Scanner.** Pasa ambos OWL por el detector de pitfalls (oops.linkeddata.es) y corrige o justifica cada hallazgo.
6. **Competency questions.** Define 10–15 preguntas de competencia (ej. "¿qué actos del procedimiento sumario tienen término y qué artículo los fija?", "¿qué dimensiones validan la capa Governance?") y demuestra que consultas SPARQL sobre las ontologías las responden. Es la prueba estándar de adecuación.
7. **Metodología de construcción.** Documenta el proceso como NeOn o Methontology (especificación → conceptualización → formalización → evaluación) — encaja retroactivamente con lo que ya hiciste.

**Criterio de éxito:** ontologías consistentes (razonador DL), sin pitfalls críticos (OOPS!), que responden sus competency questions, alineadas a un estándar legal.

---

## Orden de ejecución sugerido

| # | Acción | Fallos que ataca | Esfuerzo |
|---|--------|------------------|----------|
| 1 | Feriados judiciales + `salud-global` + cierre del ciclo al radar | 1, 5 | 2–3 días |
| 2 | Gold standard + eval del razonador | 5, 6 | 1–2 semanas (depende del abogado) |
| 3 | Protocolo scraping + snapshots + evidence[] | 1, 2 | 3–4 días |
| 4 | AHP/Delphi + sensibilidad + INTEROP homogénea | 3 | 1–2 semanas (depende de expertos) |
| 5 | IRIs/versiones + COGEP→OWL + HermiT + OOPS! + CQs | 7 | 1 semana |
| 6 | Glosario + renombrado taxonómico | 4 | 1–2 días |
| 7 | Caracterización de muestra + redacción de alcance | 6 | 1 día |

Los pasos 2 y 4 tienen dependencias externas (abogado anotador, panel de expertos): inícialos primero en paralelo con el trabajo técnico.
