# Plan — Validación de la Capa Adaptativa: implementación + UI
**Fecha:** 2026-07-13 · **Complementa:** `PLAN_ADAPTATIVIDAD.md` (implementado) y `PLAN_CORRECCION_FALLOS.md` (Fallos 1, 3, 4, 5, 6, 7)
**Principio rector:** cada aspecto debe cumplir tres condiciones verificables en la app:
1. **Evidenciable** — el usuario lo ve en la interfaz con su fundamento (artículo, fuente, hash, métrica), nunca como caja negra.
2. **Configurable** — los parámetros se fijan desde la UI (no editando JSON a mano) y se validan al guardar.
3. **Trazable** — todo cambio queda asentado en la bitácora hash-encadenada con `contexto_adaptacion` (M5, ya operativo).

---

## Organización de la UI

El tab **09 Adaptativo** gana una **sub-navegación de píldoras** (patrón ya usado en otros tabs) para no crear más tabs de nivel superior:

```
[ Ciclo ] [ Métricas ] [ Calendario ] [ Ranking ] [ Alertas ] [ Validez IA* ] [ Cambio Normativo* ] [ Trazabilidad ]
```
(*) nuevas. La rúbrica/AHP vive en el tab **04 SDS/Validación** (donde está el radar) y la verificación ontológica en el tab **07 COGEP**, porque ahí es donde el usuario mira esos artefactos.

---

## A1 — Validez del razonador: gold standard + evaluación (prioridad 1)

**Qué se implementa**
- `env/data/gold/gold_standard.json`: anotaciones `{expediente, actividad_seq, acto_correcto, veredicto_correcto, anotador, fecha, notas}` + `env/data/gold/GUIA_ANOTACION.md` (1 página).
- Endpoints: `GET/POST /api/eval/gold` (anotaciones), `POST /api/eval/run` → corre `_match_acto()` y `razonar_expediente()` contra el gold y calcula precision/recall/F1 del mapeo y exactitud del veredicto, con matriz de confusión; persiste `env/data/gold/eval_report.json` + bitácora (`tipo:"adaptacion"`).
- Si hay ≥2 anotadores: kappa de Cohen inter-anotador.

**UI (sub-pestaña "Validez IA") — el abogado anota desde la pantalla, no en JSON**
- **Modo anotación**: selector de causa → lista de actuaciones reales; por cada una, dropdown con los 16 actos de la ontología (+ "ninguno/fuera de frontera") y botones CUMPLE/ALERTA/INCUMPLE/NO_EVALUABLE. Campo anotador. Barra de progreso "N/40 anotadas · estratos: ordinario x, sumario y, monitorio z".
- **Modo resultados**: tarjetas F1 / precision / recall / exactitud del veredicto; **matriz de confusión** como heatmap; lista de errores (qué dijo el razonador vs el abogado, con enlace a la actuación); comparación línea base vs mejorado entre corridas.
- **Evidencia transversal**: chip junto a cada dictamen del tab COGEP y del detalle de ranking: `F1 0.87 · evaluado sobre N=40 (2026-07-20)` — si no hay evaluación vigente, el chip dice `sin validez medida` en ámbar. Esto convierte la limitación en transparencia.

**Configurable desde la UI**: umbral de aceptación F1 (slider, default 0.85 — si la última corrida queda debajo, banner de advertencia en todos los dictámenes); tamaño mínimo del gold por estrato; anotador activo.

**Criterio de éxito**: métricas visibles y citables; ninguna pantalla muestra un dictamen sin su chip de validez.
**Esfuerzo**: 3–4 días de app + tiempo del abogado anotador (arrancar ya el reclutamiento).

## A2 — Gestión del Cambio Normativo / Jurisprudencial (M3)

**Qué se implementa**
- KB versionada: cada regla gana `vigencia_desde`, `vigencia_hasta`, `fuente {tipo, registro_oficial|sentencia, url}`; `meta.version`. Nuevo `env/data/kb_changelog.json` (append-only).
- El razonador aplica la **regla vigente a la fecha del acto** (aplicación temporal correcta de la norma).
- Endpoints: `GET /api/adaptativo/kb-changelog`, `POST /api/adaptativo/kb-cambio` (valida que la regla exista en la ontología y que las fechas sean coherentes antes de aceptar — guardrail), `GET /api/adaptativo/impacto?cambio=` (re-corre el corpus con KB anterior vs nueva y devuelve el delta de veredictos).

**UI (sub-pestaña "Cambio Normativo")**
- **Editor de regla**: formulario (término_días, artículo, texto de la norma, vigencia, fuente RO/sentencia con URL) — el usuario registra una reforma sin tocar archivos; validación en vivo.
- **Timeline** de cambios con diff antes/después (patrón visual de la bitácora).
- Botón **"Re-evaluar impacto"** → tabla de causas cuyo dictamen cambia (CUMPLE↔INCUMPLE) con el delta del índice global: *esto evidencia la adaptación normativa en acción*.
- Badge global `KB v2.1 · vigente desde 2026-01-15` en la cabecera de los tabs COGEP y Adaptativo.

**Configurable**: todo el contenido normativo (reglas, vigencias, fuentes). **Criterio de éxito**: registrar una reforma simulada y ver el impacto propagarse a ranking, alertas y radar. **Esfuerzo**: 3–4 días.

## A3 — Rúbrica, evidencia por dimensión y pesos AHP (Fallos 1 y 3)

**Qué se implementa**
- `env/data/rubrica_dimensiones.json`: por cada una de las 9 dimensiones, niveles 0–100 con criterios observables; `evidence[]` por dimensión en `SDT_CJ.json` con `source_ref` a los snapshots ya capturados (reutiliza el sistema de evidencia existente).
- `POST /api/ahp`: cada experto llena la matriz de comparación por pares (escala Saaty 1–9); el backend calcula pesos por eigenvector y **razón de consistencia CR**, rechazando CR > 0.10; guarda `env/data/pesos_ahp.json`. `psi()` lee los pesos desde ahí (deja de estar hard-coded).
- `GET /api/sensibilidad`: perturba pesos ±10 %/±20 % y devuelve datos para gráfico tornado + estabilidad del nivel de madurez.

**UI (en tab 04, junto al radar)**
- Clic en una dimensión del radar → **drawer de evidencia**: nivel de rúbrica aplicado, criterios cumplidos, y las evidencias enlazadas a su snapshot (con verificación SHA-256 en un clic) — score "evidenciado" vs "declarado" con badge distinto.
- **Editor AHP**: matriz de comparación por pares interactiva; CR calculado en vivo (verde ≤0.10, rojo si no); cada experto guarda su matriz con su nombre; pesos agregados visibles con procedencia.
- **Gráfico tornado** de sensibilidad + semáforo "nivel de madurez estable ante ±10 %: SÍ/NO".

**Configurable**: juicios AHP por experto, rúbrica editable (con asiento en bitácora). **Esfuerzo**: 4–5 días de app + panel de expertos en paralelo (Delphi si hay poco acceso).

## A4 — Verificación ontológica COGEP (Fallo 7)

**Qué se implementa**
- `env/tools/kb2owl.py` (owlready2): `cogep_kb.json` → `COGEP_ontology.owl` (clases Procedimiento/Etapa/ActoProcesal/Término/Sujeto, object properties, individuos anotados con artículo). Namespace unificado con MALTG.
- `GET /api/cogep/owl/verificacion`: corre el razonador DL (HermiT vía owlready2) → consistencia, clases insatisfacibles; persiste el reporte.
- `env/data/competency_questions.json`: 10–15 CQs con su consulta SPARQL; `GET /api/cogep/cq` las ejecuta y devuelve resultado + estado (responde/no responde).

**UI (en tab 07 COGEP, panel "Verificación Ontológica")**
- Tarjetas: consistencia ✔/✖, clases insatisfacibles (lista), fecha de última verificación, hash del OWL; botón "Re-verificar".
- Lista de **competency questions** con su respuesta desplegable y estado verde/rojo — *evidencia de que la ontología responde lo que la tesis dice que responde*.
- Enlace de descarga del OWL + resultado OOPS! (se corre en oops.linkeddata.es y se registra el reporte manualmente en la UI).

**Configurable**: añadir/editar CQs desde la UI. **Esfuerzo**: 4–5 días.

## A5 — Taxonomía + caracterización de la muestra (Fallos 4 y 6, rápidos)

- **Renombrado**: "Gemelo Digital Estructural" → **"Modelo Digital Estructural (SDT)"** en UI y `meta.title` de los JSON; tab del razonador → **"Sombra Digital Cognitiva"**; tooltip con la taxonomía de Kritzinger et al. (2018) en cada aparición del término. Nota visible: "gemelo pleno = retroalimentación a e-SATJE (trabajo futuro)".
- **Muestra**: `GET /api/adaptativo/muestra` → caracterización desde `/data/LegalCase` (N por procedimiento, provincia = dígitos 1–2 de la causa, año, estado). Panel en el tab Adaptativo con la tabla + declaración fija: *"muestreo intencional no probabilístico estratificado; permite generalización analítica, no inferencia poblacional"* — visible junto al índice global 36.7 para acotar qué representa.
- **Configurable**: dimensiones de estratificación de la tabla. **Esfuerzo**: 1–2 días.

---

## Orden de ejecución

| Fase | Aspecto | Dependencia externa | Esfuerzo app |
|------|---------|---------------------|--------------|
| F1 | A1 pantalla de anotación + endpoints eval | abogado anotador (iniciar ya) | 3–4 días |
| F2 | A5 taxonomía + muestra (mientras el abogado anota) | — | 1–2 días |
| F3 | A2 cambio normativo | — | 3–4 días |
| F4 | A1 resultados (F1/matriz/chips) con las anotaciones reales | gold completo | 1–2 días |
| F5 | A3 rúbrica + AHP + sensibilidad | panel de expertos | 4–5 días |
| F6 | A4 COGEP→OWL + HermiT + CQs | — | 4–5 días |

**Regla transversal de cierre**: al terminar cada fase, la pregunta de aceptación es la misma — *¿puede el usuario ver el aspecto funcionando en la interfaz, cambiar su configuración, y encontrar el asiento correspondiente en la bitácora?* Si alguna de las tres respuestas es no, la fase no está cerrada.
