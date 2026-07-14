# Plan — Capa Adaptativa MALTG v3: UI + Arquitectura
**Fecha:** 2026-07-13 · **Complementa:** `PLAN_CORRECCION_FALLOS.md` (Fallos 1, 4, 5)
**Objetivo:** hacer defendible el término **"Adaptativa"** del título de tesis, con representación explícita en la interfaz gráfica.

---

## 0. Concepto rector: ciclo MAPE-K sobre ontologías

La adaptatividad se formaliza con el patrón **MAPE-K** (Monitor → Analyze → Plan → Execute, sobre una base de **K**nowledge), estándar de sistemas autonómicos (IBM, Kephart & Chess 2003). Encaja exacto con lo ya construido:

| Fase MAPE-K | Artefacto del proyecto |
|---|---|
| **Monitor** | Expedientes SATJE (`/data/LegalCase`), scraping CJ, actividades del juez |
| **Analyze** | Razonador COGEP (`razonar_expediente`), detector de drift (nuevo) |
| **Plan** | Recalibración de scores del radar + alertas de gobernanza (nuevo) |
| **Execute** | Actualización de `SDT_CJ.json` / radar + panel de alertas (nuevo) |
| **Knowledge** | Ontologías MALTG + COGEP = **frontera de lo expresable** (guardrails) |

**Regla de oro (anti-alucinación):** ninguna fase puede producir una salida que no sea un individuo/relación de las ontologías. La IA no "opina": clasifica dentro del vocabulario cerrado (acto ∈ `cogep_kb.actos`, regla ∈ `cogep_kb.reglas`, dimensión ∈ MALTG). Lo que cae fuera se reporta como `fuera_de_frontera`, nunca se inventa.

---

## 1. Decisión de UI

**Nuevo tab "Adaptativo"** (Centro de Gobernanza Adaptativa) en `frontend/index.html`, junto a los 8 existentes (`maltg, ontology, dt, methodology, workflow, cogep, simulacion, bitacora`; el tab `styles` no se considera). Además, **indicadores transversales** (badges) en tabs existentes para que la adaptación sea visible donde ocurre:

- Tab **Validación/DT**: badge "score empírico ↺ recalculado el {fecha} desde N causas" junto al radar.
- Tab **COGEP**: cada dictamen muestra su bloque de metadatos de contexto (ver M5).
- Tab **Workflow**: overlay de drift sobre el grafo BPMN (ver M2).

Layout del tab Adaptativo (grid glassmorphism, mismo sistema de estilos):

```
┌──────────────────────────────────────────────────────────────┐
│  CICLO MAPE-K (diagrama animado: fase activa iluminada)      │
├────────────────┬────────────────┬────────────────────────────┤
│ M1 Variabilidad│ M2 Process     │ M6 Seguridad Cognitiva     │
│ del contexto   │ Drift          │ (alertas fuera de ley)     │
├────────────────┴────────────────┼────────────────────────────┤
│ M3 Cambio Normativo (timeline)  │ M4 Guardrails (semáforo)   │
├─────────────────────────────────┴────────────────────────────┤
│ M5 Trazabilidad de la Adaptación (tabla de eventos + hash)   │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Módulos

### M1 — Variabilidad del Contexto Fáctico (datos de entrada)

**Qué mide:** cuánto varían las actividades reales del juez frente al flujo canónico COGEP. Insumos ya disponibles por actividad: `TipoProvidencia`, `NombreProvidencia`, `FechaProvidencia`, `Login` (juez/secretario), `Secuencia`, `IdGrafoFlujoEstructura`, `nombreestado`.

**UI:**
- Selector de causa/procedimiento + **matriz de calor**: filas = actos canónicos del procedimiento, columnas = causas; celda = presente / ausente / extra (no canónico).
- **Índice de Variabilidad Fáctica (IVF)** 0–100 por causa: `IVF = 100 · (actos_no_canónicos + actos_faltantes) / actos_esperados`.
- Distribución de IVF por procedimiento (histograma) y por judicatura (`IdJudicatura`).

**Backend:** `GET /api/adaptativo/variabilidad?file=` y `GET /api/adaptativo/variabilidad-global`. Reutiliza `_match_acto()`: acto mapeado = canónico; no mapeado = variabilidad.

**Datos:** ninguno nuevo (usa `LegalCase` + `cogep_kb.procedimientos`).

### M2 — Deriva del Proceso (Process Drift / dilación)

**Qué detecta:** patrones de actividades repetidas que dilatan el proceso. Detectores (conformance checking ligero sobre la traza `actividades[]` ordenada por `Secuencia`):

1. **Loops:** mismo `NombreProvidencia` (normalizado) ≥ k veces en la misma etapa (ej. diferimientos de audiencia, "nuevo señalamiento").
2. **Ping-pong:** alternancia A→B→A→B entre dos actos.
3. **Estancamiento:** el criterio primario es el marco legal: gap de días hábiles entre actos consecutivos que excede el término que el COGEP fija para ese acto (`cogep_kb.reglas`, con artículo citable; usa `business_days()` ya con feriados). Solo para actos sin término legal definido se usa un umbral estadístico de respaldo (p95 del mismo procedimiento), rotulado como "referencial, sin fundamento normativo".
4. **Retroceso de etapa:** acto de etapa i después de actos de etapa j>i sin recurso que lo justifique.

**UI:**
- Overlay en el grafo del tab Workflow: nodos con loop en **ámbar pulsante**, aristas de retroceso en rojo punteado.
- **Índice de Deriva (IDP)** por causa y agregado por judicatura/juez (`Login`) — tabla ranking "focos de dilación" con severidad.
- Sparkline temporal: derivas detectadas por trimestre (¿el patrón crece?).

**Backend:** `GET /api/adaptativo/drift?file=` y `GET /api/adaptativo/drift-global`. Nuevo `env/tools/drift_detector.py` (importable desde `main.py`).

**Cuidado metodológico:** el ranking por `Login` se rotula "patrón de tramitación", no "conducta del juez" — la causa de la dilación puede ser de las partes. La UI debe mostrar el disclaimer.

### M3 — Gestión del Cambio Normativo / Jurisprudencial

**Qué gestiona:** el COGEP y la jurisprudencia (CC/CNJ) cambian; la KB debe versionarse y el sistema debe **adaptarse re-evaluando** lo afectado.

**Modelo de datos:** `cogep_kb.json` gana `meta.version`, `meta.vigencia_desde`, y cada regla: `{vigencia_desde, vigencia_hasta, fuente: {tipo: "reforma"|"jurisprudencia", registro_oficial|sentencia, url, fecha}}`. Nuevo `env/data/kb_changelog.json`: lista de cambios `{fecha, regla_id, campo, antes, despues, fuente, autor}`.

**UI:**
- **Timeline vertical** de cambios normativos (estilo bitácora) con diff antes/después de la regla.
- Al registrar un cambio: botón **"Re-evaluar impacto"** → lista de causas cuyo dictamen cambia con la nueva regla (re-corre el razonador con ambas versiones y muestra el delta CUMPLE↔INCUMPLE).
- Badge en tab COGEP: "KB v{X} · vigente desde {fecha}".

**Backend:** `GET /api/adaptativo/kb-changelog`, `POST /api/adaptativo/kb-cambio` (valida contra ontología antes de aceptar), `GET /api/adaptativo/impacto?cambio_id=`. El razonador selecciona la versión de regla vigente a la `FechaProvidencia` del acto (aplicación temporal correcta de la norma).

### M4 — Guardrails: ontologías como Restricciones de Frontera y Control de Deriva de la IA

**Principio:** la ontología define el **espacio legítimo de salidas**. Tres guardrails verificables:

1. **Frontera de vocabulario:** toda clasificación (`_match_acto`, chat, análisis PDF) debe resolver a un `acto_id` existente; si el score de matching < umbral → salida `{status:"fuera_de_frontera", accion:"derivar a humano"}`, jamás una respuesta inventada.
2. **Frontera de inferencia:** todo dictamen debe citar `regla_id` + artículo COGEP existente en la KB; el endpoint rechaza dictámenes sin cadena regla→artículo (verificación automática, no confianza en el generador).
3. **Control de deriva del modelo:** job que compara la distribución de matches sobre el corpus entre versiones de KB/razonador (índice de estabilidad tipo PSI); si >20 % de los dictámenes históricos cambia sin cambio normativo que lo explique → alerta "deriva no justificada".

**UI:**
- **Semáforo de frontera** en cada respuesta IA (chat, juicio, análisis): 🟢 dentro de ontología (muestra la cadena acto→regla→artículo clicable), 🟡 confianza baja (respuesta con advertencia), 🔴 fuera de frontera (respuesta rechazada + texto fijo "requiere criterio humano").
- Panel en tab Adaptativo: % de consultas dentro/fuera de frontera, tendencia, y contador de "respuestas rechazadas" — **mostrar los rechazos como virtud del sistema**, es el argumento anti-alucinación de la tesis.

**Backend:** middleware `guardrail_check(salida)` aplicado a `/api/cogep/juicio`, `/api/cogep/chat`, `/api/cogep/analisis`; `GET /api/adaptativo/guardrails-stats`.

### M5 — Trazabilidad de la Adaptación (Metadatos de Contexto)

**Qué garantiza:** cada salida y cada adaptación es reproducible — se sabe con qué conocimiento y con qué datos se produjo.

**Bloque de metadatos** (adjunto a todo dictamen/score/alerta):

```json
"contexto_adaptacion": {
  "kb_version": "3.1", "kb_hash": "sha256:…",
  "ontologia_version": "MALTG 2.5 / COGEP 1.2",
  "razonador_version": "v3", "feriados_dataset": "2026-06",
  "evidencia_run": "2026-07-08_184824",
  "causa_hash": "sha256:…", "timestamp": "…",
  "trigger": "cambio_normativo|nueva_causa|recalculo_manual"
}
```

Cada evento de adaptación (recalibración del radar, cambio de KB, re-evaluación de impacto) se registra en la **bitácora hash-encadenada existente** (`bitacora_log`) con `tipo:"adaptacion"` — no se crea infraestructura nueva.

**UI:** tabla filtrable de eventos de adaptación en el tab Adaptativo (fecha, trigger, qué cambió, hash, verificación de cadena ✔); en tab COGEP, icono ⓘ junto a cada dictamen que despliega el bloque de contexto.

### M6 — Seguridad Cognitiva (alertas de actos fuera de ley)

**Qué es:** la capa que protege al usuario de conclusiones erróneas y **alerta activamente** cuando un expediente presenta aspectos fuera de la ley. Sintetiza M1+M2+M4:

**Tipología de alertas** (cada una trazable a artículo COGEP):

| Nivel | Alerta | Fuente |
|---|---|---|
| 🔴 Crítica | Término legal vencido sin acto (Art. 73 ss.) | Razonador |
| 🔴 Crítica | Acto no previsto en el procedimiento (posible nulidad, Art. 107) | M1 frontera |
| 🟠 Alta | Patrón dilatorio detectado (≥k diferimientos) | M2 drift |
| 🟠 Alta | Dictamen emitido con KB desactualizada frente a reforma vigente | M3 |
| 🟡 Media | Salida IA fuera de frontera ontológica (derivada a humano) | M4 |

**Principio de seguridad cognitiva en la UI:** toda alerta muestra (a) el hecho observable (fechas, actos), (b) la regla que lo fundamenta (artículo clicable), (c) la incertidumbre ("basado en matching léxico, F1={valor medido}"), y (d) el descargo fijo: *"Indicador de apoyo — no constituye asesoría jurídica ni prejuzga la conducta procesal"*. Nunca lenguaje conclusivo tipo "el juez incumplió".

**UI:** panel de alertas en el tab Adaptativo (cards por severidad, filtro por causa/judicatura/tipo) + contador global en la cabecera del dashboard. **Backend:** `GET /api/adaptativo/alertas` (agrega salidas de M1, M2, M3, M4 sobre todo `/data/LegalCase`).

---

## 3. Cierre del ciclo (lo que convierte todo en "adaptativo")

`GET /api/cogep/salud-global` (del Fallo 1) se implementa como la fase **Analyze→Plan** del MAPE-K: índice empírico = actos en plazo / actos evaluables (con feriados, M1 y M2 descontando causas atribuibles a las partes). `compute_validation()` toma ese índice para la dimensión Operational — **el radar deja de ser declarado y pasa a latir con los expedientes**. Cada recálculo queda en bitácora (M5). Ese es el argumento central del capítulo: *el modelo de gobernanza se adapta porque sus scores se recalculan desde la realidad procesal, dentro de la frontera que fijan las ontologías*.

---

## 4. Fases de implementación

| Fase | Entregable | Módulos | Esfuerzo |
|---|---|---|---|
| F1 | `feriados_judiciales.json` + `business_days()` + `/api/cogep/salud-global` + cierre al radar | base, M5 | 2–3 días |
| F2 | Tab "Adaptativo" con diagrama MAPE-K + panel M5 (bitácora de adaptación) | UI, M5 | 2 días |
| F3 | `drift_detector.py` + M1 + M2 + overlay en Workflow | M1, M2 | 3–4 días |
| F4 | Guardrails middleware + semáforo de frontera en COGEP/chat | M4 | 2–3 días |
| F5 | Versionado KB + changelog + re-evaluación de impacto | M3 | 3 días |
| F6 | Panel de Seguridad Cognitiva (agrega alertas de todos los módulos) | M6 | 2 días |

Orden recomendado: F1 → F2 → F3 → F4 → F6 → F5 (F5 puede ir en paralelo desde F3).

## 5. Mapeo a la tesis

- **"Adaptativa"** → MAPE-K + cierre del ciclo (§3) — responde al Fallo 1.
- **"basada en IA"** → razonador simbólico con guardrails ontológicos y validez medida (M4 + gold standard del Fallo 5) — IA neurosimbólica/acotada, no caja negra.
- **"Gobernanza"** → alertas y recalibración como instrumentos de gobernanza (M3, M6).
- **"Flujos Procesales"** → variabilidad y drift sobre trazas BPMN reales (M1, M2).
- Marco teórico a citar: MAPE-K (Kephart & Chess 2003), process drift/conformance checking (van der Aalst), ontology-grounded guardrails (neuro-symbolic AI), taxonomía de gemelos (Kritzinger 2018, ya en Fallo 4).
