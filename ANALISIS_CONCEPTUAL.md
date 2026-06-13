# Análisis Conceptual — MALTG LegalTech Validator
**Fecha:** 2026-06-11 · **Alcance:** revisión de arquitectura, ontología, gemelo digital, motor de validación y flujo procesal.

---

## 1. Fallos conceptuales detectados

### F1. La consolidación Tab 01 → Tab 03 está incompleta (el fallo más importante)
`1_MALTG.json` (Tab 01) define **5 capas**: Strategic, Governance & Compliance, Operational, Technology Integration y Foundation. Sin embargo, `MALTG_onto.owl` (Tab 03) solo modela **3 dominios**: Foundation, Technology Integration y LegalTech Domain. Las capas Strategic, Governance & Compliance y Operational **no existen como clases OWL**, por lo que la afirmación "las capas se consolidan en una ontología" no se sostiene formalmente. Además, el Tab 01 declara ITIL dentro del Foundation Layer (TOGAF–COBIT–ITIL–NIST CSF), pero no hay ninguna clase ni dimensión de validación ITIL: el motor valida 9 dimensiones y ninguna cubre Operational (Workflows–Services–Incidents–Changes), que es justamente donde vive el flujo procesal.

**Corrección sugerida:** completar la ontología con las clases de las 5 capas (aunque sea con sub-conceptos mínimos) y añadir dimensiones ITIL/Operational, o justificar explícitamente en la tesis por qué la validación se restringe a Foundation + Technology + LegalTech.

### F2. Validación circular (autorreferencial)
Los puntajes de madurez (`maltg:score`) son anotaciones declaradas por el propio autor, y el mapeo `maltg_ref` del gemelo digital también es manual. El sistema mide la conformidad de "Judicatura Ecuador" contra etiquetas que el mismo modelador asignó: **no hay capa de evidencia**. Un revisor de tesis lo detectará de inmediato.

**Corrección sugerida:** introducir una fuente de evidencia independiente por dimensión. La más natural ya está en el proyecto: los **expedientes reales** (`/data/LegalCase`). El cumplimiento de plazos COGEP medido sobre causas reales es evidencia objetiva y verificable de la dimensión Operational/LegalTech (esto es lo que materializa la nueva arista procesal).

### F3. El "gemelo digital" es, en rigor, un *modelo* digital
Según la taxonomía aceptada (Kritzinger et al., 2018: *digital model → digital shadow → digital twin*), un gemelo exige flujo de datos automático desde el sistema físico/real. `dt_arch.json` es estático y no recibe telemetría del sistema real (SATJE/eSATJE): es un **modelo digital estructural**. En cambio, los expedientes JSON sí son datos reales del sistema judicial: al conectarlos al flujo BPMN y evaluarlos contra el COGEP, esa parte sí alcanza el nivel de **digital shadow** (datos reales → representación, sin retroalimentación). Conviene usar esta terminología con precisión en la tesis: *gemelo estructural (modelo) + gemelo cognitivo-procesal (shadow)*.

### F4. Métrica Ψ con pesos arbitrarios e INTEROP inconsistente
Ψ(d) = 0.4·root + 0.6·subs no tiene justificación ni análisis de sensibilidad. La dimensión INTEROP usa una fórmula ad-hoc distinta (0.60·OD + 0.30·SEC + 1.25·cross-links, tope 10) que rompe la homogeneidad del modelo formal ⟨Ω, Δ, Γ, Ψ, δ⟩ y **doble-cuenta** los `dt_refs` de Open Data y Security. Documentar los pesos (p. ej. criterio experto tipo AHP/Delphi) o ejecutar sensibilidad ±10 %.

### F5. Incoherencias de identidad semántica y versión
- `1_MALTG.json` usa el namespace `https://maltg.arch/onto#`; el OWL usa `http://maltg.arch/onto#`. En linked data son IRIs **distintas**: la consolidación semántica entre Tab 01 y Tab 03 queda rota formalmente.
- Versiones divergentes: docker-compose etiqueta 2.5.0, la API declara 3.0.0, el OWL dice 2.4.0 y su `versionInfo` 3.0.0-legaltech.
- En `METHODOLOGY`, la definición de δ contiene un error tipográfico: "δ(d) = score_Ω(d) − score_Ω(d)·Ψ(d) = …" está bien al final, pero la primera igualdad aparece truncada en la redacción.

### F6. Marco regulatorio eurocéntrico para validar una judicatura ecuatoriana
La dimensión LegalTech verifica GDPR, eIDAS y NIS2 — normativa **europea**. Para "Judicatura Ecuador" el marco aplicable es: **LOPDP** (Ley Orgánica de Protección de Datos Personales, 2021), **Ley de Comercio Electrónico, Firmas Electrónicas y Mensajes de Datos**, **EGSI** (Esquema Gubernamental de Seguridad de la Información), COIP/COFJ y resoluciones del Consejo de la Judicatura. Mantener GDPR/eIDAS como referente comparado está bien, pero la validación de cumplimiento debe citar la norma nacional.

### F7. El flujo procesal (Tab 06) estaba aislado de la gobernanza
El workflow BPMN y los expedientes no se conectaban a ninguna dimensión ni concepto ontológico: la "arista procesal" no retroalimentaba el modelo. Tampoco existía noción de **plazos**: el COGEP define términos en *días hábiles* (Art. 73 COGEP), y el sistema no calculaba ni comparaba tiempos. Esto se corrige con la base de conocimiento COGEP (`cogep_kb.json`), el razonador de plazos y el dashboard de salud del juicio.

### F8. Tecnologías declaradas pero no materializadas
AI, Blockchain y Open Data puntúan en el radar de validación, pero no existía ninguna implementación ni demostración. Brecha entre lo medido y lo demostrable. Se materializan así (ver §3).

### F9. Observaciones técnicas menores
CORS abierto (`*`) y API sin autenticación (aceptable para demo local, debe declararse como limitación); el orden cronológico de actividades depende de comparación de strings de fecha (válido solo por formato ISO); el contenedor monta `/data` como solo lectura pero el upload de PDF requerirá escritura temporal (se usa memoria); `healthcheck` no verifica los archivos de workflow/expedientes.

---

## 2. Arquitectura conceptual corregida (cómo contar la historia)

1. **Capa de referencia (Ω):** las 5 capas del Tab 01 + dominio LegalTech, consolidadas en la ontología MALTG (Tab 03), con normativa nacional como sub-conceptos de Governance & Compliance.
2. **Gemelo estructural (Δ):** el microservicio (Tab 04) — *modelo digital* del sistema objetivo, validado por Γ/Ψ/δ (Tab 05).
3. **Gemelo cognitivo-procesal (nuevo, Tabs 06 y 09):** el flujo BPMN del COGEP + expedientes reales = *digital shadow* del proceso judicial. Su "conocimiento" es la ontología COGEP (`cogep_kb.json`): procedimientos → etapas → actos procesales → términos → artículos.
4. **Razonador jurídico simbólico:** motor de reglas determinista que evalúa cada actuación judicial contra los términos del COGEP y emite un **dictamen fundamentado con citas de artículos** (juicio de valor explicable — XAI, sin alucinaciones, defendible académicamente como razonamiento neuro-simbólico en su variante simbólica).
5. **Evidencia → gobernanza:** la salud procesal agregada de las causas alimenta la dimensión Operational/LegalTech del radar, cerrando el ciclo y eliminando la circularidad de F2.

## 3. Materialización de AI · Blockchain · Open Data (ejemplos pequeños y reales — Tab 06)

| Tecnología | Implementación real en la app | Qué demuestra |
|---|---|---|
| **AI** | Razonador COGEP: mapea cada providencia del expediente a un acto procesal de la ontología, calcula días hábiles transcurridos y dictamina CUMPLE / ALERTA / INCUMPLE citando el artículo (p. ej. Art. 146: calificación ≤ 5 días; Art. 291: contestación 30 días; Art. 333.4: audiencia única ≤ 30 días; Art. 93: sentencia escrita ≤ 10 días; Art. 257: apelación ≤ 10 días). También analiza PDFs de actuaciones subidos por el usuario. | IA jurídica explicable sobre conocimiento legal formalizado |
| **Blockchain** | Ledger de integridad: cada actuación del expediente se encadena con SHA-256 (`hash_i = H(actividad_i ‖ hash_{i-1})`), con verificación en vivo y simulación de manipulación que rompe la cadena visualmente. | Inmutabilidad y no-repudio del expediente (notarización tipo DLT) |
| **Open Data** | Exportación del expediente como **JSON-LD** (vocabulario schema.org + MALTG) y **CSV**, con metadatos DCAT y referencia al portal público (consultas.funcionjudicial.gob.ec). | Interoperabilidad y datos abiertos judiciales |

## 4. Mejora del flujo procesal (Tab 06) — implementada
- **Dirección y movimiento:** aristas del recorrido de la causa animadas (flujo direccional tipo "marching ants"), reproducción paso a paso del recorrido con token animado.
- **Alertas de plazo:** nodos cuyo acto excedió el término COGEP pulsan en rojo con etiqueta "+N días"; los que cumplen, en verde.
- **Dashboard Salud del Juicio:** semáforo global (índice 0–100 = actos en plazo / actos evaluables), desglose por acto con artículo citado y días hábiles vs. término.
- **Dictamen IA por actividad/PDF:** al abrir una actividad (o subir el PDF de la providencia) el razonador emite el juicio de valor sobre la actuación del juez.

## 5. Nuevo Tab 09 — Ontología COGEP
Grafo navegable Procedimiento → Etapa → Acto procesal → Término → Artículo (D3), generado desde `data/cogep_kb.json`, con panel de razonamiento que ejecuta el dictamen sobre cualquier expediente. La KB es editable: agregar un artículo/plazo nuevo actualiza ontología y razonador sin tocar código.

## 6. Limitaciones a declarar en la tesis
El cálculo de días hábiles excluye fines de semana pero no feriados judiciales ni suspensiones de término; el mapeo providencia→acto usa heurística léxica (keywords) validable manualmente; el ledger demuestra el mecanismo de integridad pero no es una red DLT distribuida; el razonador cubre los procedimientos ordinario, sumario y ejecución (extensible).
