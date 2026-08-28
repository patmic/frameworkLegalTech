# Revisión editorial — *LegalShadow: An Ontology-Guided Digital Shadow Architecture for Semantic Validation of LegalTech Ecosystems*

**Manuscrito:** `ICI2ST_LegalShadow_Main.tex` (365 líneas, plantilla MDPI `engproc/proceedingpaper`)
**Rol:** revisor par + editor científico
**Fecha de revisión:** 9 de agosto de 2026
**Recomendación global:** **Aceptar con revisiones menores–moderadas** (*minor–major revision*)

---

## 1. Veredicto en una página

El paper es sólido, original y tiene una tesis nítida y defendible: *la madurez declarativa no equivale a gobernanza accionable por máquina*. La contribución (Ψ como verificador operacional del anclaje ontología–artefacto) responde a un hueco real señalado por Karabulut et al. y está bien posicionada frente a Kritzinger. La aritmética es **internamente consistente**: verifiqué las 10 filas de la Tabla 1, los agregados, el control sintético y el barrido de sensibilidad, y todo cuadra (ver §2).

Los problemas no son de fondo sino de **alineación y trazabilidad interna**: hay tres inconsistencias reales entre figuras y tabla, una ambigüedad de notación que un revisor exigente atacará, y un desalineamiento título↔caso de estudio. Ninguno exige rehacer experimentos.

| Bloque | Alineación | Nota |
|---|---|---|
| Título ↔ Abstract | Parcial | "LegalTech Ecosystems" vs. ecosistema judicial público |
| Abstract ↔ Resultados | **Buena** | todas las cifras del abstract se verifican en §4 |
| Modelo formal ↔ Tabla 1 | **Buena** | aritmética exacta salvo redondeos ≤0.21 |
| Figura 1 ↔ Figura 2b ↔ Tabla 1 | **Inconsistente** | ver H-1, H-2 |
| Resultados ↔ Conclusiones | **Buena** | sin claims no soportados |
| Limitaciones ↔ Claims | **Buena** | honestas y completas |
| Disponibilidad de datos ↔ claims de auditabilidad | **Contradictoria** | ver H-4 |

---

## 2. Verificación numérica independiente (recalculada)

Recomputé todo el aparato desde los valores de la Tabla 1. **Resultado: consistente.**

- `sds(d) = onto(d)·Ψ(d)` — correcto en 10/10 filas (desvío máx. 0.21 en LegalTech, ver H-7).
- `δ(d) = onto(d) − sds(d)` — correcto en 10/10 filas.
- `Onto_global = 73.94 ≈ 73.9` ✓ · `SDS_global = 25.76 ≈ 25.8` ✓
- `Ψ_global = 25.76/73.94 = 0.3484 ≈ 0.349` ✓ (34.9 % es redondeo al alza de 34.84 %; aceptable)
- Brecha agregada `48.18 ≈ 48.1` y `65.2 % ≈ 65.1 %` ✓
- Control sintético: `66.87 ≈ 66.9`, `66.87/73.94 = 90.4 % ≈ 90.5 %` ✓, residual `7.0` ✓
- Índice declarativo: `(28+42+55+58)/4 = 45.75 ≈ 46/100` ✓ → Nivel 3 (41–60) ✓
- Corpus: `170/187 = 90.91 % ≈ 90.9 %` ✓ · `50/131 = 38.17 % ≈ 38.2 %` ✓
- Barrido de sensibilidad: reconstruí las fracciones `|S_d∩R|/|S_d|` implícitas (0.25, 0, 0.20, 0, 0.50, 0, 0.333, 0.45, 0.75, 1.00) y **reproduje exactamente 26.9 → 23.9** para `w_r ∈ [0.10, 0.90]`. ✓
- Fracción TOGAF implícita = 0.333 = **2/6**, coherente con la Figura 1. ✓

**Conclusión:** los números son reproducibles y no hay errores de cálculo. Esto es un punto fuerte que conviene explotar (ver R-8).

---

## 3. Hallazgos críticos (deben corregirse antes de publicar)

### H-1 · La Figura 2b contradice la Tabla 1 y omite una dimensión
La esfera celeste muestra las constelaciones como **binarias** (encendida/apagada) y describe: *"Open data, interoperability and LegalTech light up; TOGAF, COBIT, ITIL, NIST CSF, AI and DLT remain dim."*

Dos problemas:

1. **Falta "Security posture"** — la figura tiene 9 constelaciones, la Tabla 1 tiene 10 dimensiones. Seguridad (Ψ = 0.30, δ = 56.3) simplemente no aparece.
2. **Contradicción sustantiva**: TOGAF (Ψ = 0.20, 2/6 subconceptos), AI (0.15), NIST (0.12) y Seguridad (0.30) se pintan **completamente apagadas**, pero la Tabla 1 dice que sí tienen concepto(s) anclados en `R`. La figura afirma cobertura cero donde la tabla afirma cobertura parcial.

Esto es grave porque el argumento central del paper (§2, línea 116) es precisamente que **Ψ distingue "práctica incompleta" de "práctica ausente"** — y la figura estrella del paper borra esa distinción.

> **Corrección:** encender parcialmente las constelaciones según la fracción real (TOGAF 2/6, AI 1/4, NIST 1/5, Seguridad 2/4), añadir la constelación de Seguridad, y reescribir el caption: *"Open data, interoperability and LegalTech are substantially lit; TOGAF, NIST CSF, AI and security are only partially lit; COBIT, ITIL and DLT remain entirely dim."*

### H-2 · Figura 1 y Figura 2b se contradicen en el tamaño de S_d
- Fig. 1: TOGAF con **6** subconceptos, ITIL con **5**.
- Fig. 2b: TOGAF con **4** estrellas, ITIL con 5, y 40 estrellas totales frente a las **131 clases** que declara el caption ("50 of 131 classes lit").

> **Corrección:** unificar TOGAF a 6 nodos en ambas figuras y añadir al caption de la Fig. 2b la palabra **"schematic"**: *"Schematic rendering; star counts are illustrative, not one-to-one with the 131 ontology classes."* Sin esa aclaración, un revisor contará estrellas.

### H-3 · Ambigüedad de notación en el barrido de sensibilidad (§2, línea 101)
> *"sweeping w_r∈[0.10,0.90] moves the global score only from 26.9 to 23.9"*

"The global score" es ambiguo: el lector viene de leer 34.9 % y verá 26.9/23.9 como una tercera cifra sin unidad. Son valores de **SDS_global**, no de Ψ_global.

> **Corrección exacta (números verificados):** *"…moves SDS_global only from 26.9 to 23.9 (equivalently, Ψ_global from 36.3 % to 32.3 %), and leaves the top of the remediation agenda unchanged."*

### H-4 · La disponibilidad de datos contradice el claim de auditabilidad
El paper construye su valor sobre provenance criptográfica, ledger hash-encadenado y re-ejecución por terceros. Pero `\dataavailability` dice: *"available from the corresponding author on request"* — al mismo tiempo que da un repositorio público de GitHub y la introducción cita un depósito Zenodo `\cite{paccha2026zenodo}`.

Un revisor lo marcará como contradicción directa entre el discurso y la práctica.

> **Corrección:** eliminar "on request". Depositar ontología OWL, shadows JSON-LD fechados y manifiestos SHA-256 en Zenodo con DOI, y citarlo. Añadir el hash de cabeza del ledger (`6c7d2847932a606f`) al enunciado para que sea verificable.

### H-5 · Comparación 46/100 vs. 34.9 % — bases distintas sin declararlo
Es **el titular del paper** y es el flanco más atacable. El 46/100 se calcula sobre **cuatro** dimensiones declarativas (interoperabilidad de datos 28, arquitectura de integración 42, transformación declarada 55, cumplimiento normativo 58); el 34.9 % se calcula sobre **diez** dimensiones ontológicas. No hay mapeo explícito entre ambos conjuntos.

Tal como está, el contraste es formalmente *apples-to-oranges* y un revisor puede pedir retirar la afirmación central.

> **Corrección (dos frases, sin experimentos nuevos):**
> 1. En el abstract: *"…yields a **four-dimension** declarative maturity index of 46/100 (Level 3), yet **ten-dimension** semantic coverage reaches only Ψ_global = 34.9 %."*
> 2. En §4, tras el párrafo de madurez declarativa, añadir una frase que justifique por qué las cuatro dimensiones declarativas son un superconjunto/subconjunto reconocible de las diez, o bien reportar además Ψ restringido a esas cuatro dimensiones. Lo segundo es más fuerte y el dato ya existe.

---

## 4. Hallazgos mayores (recomendados)

### H-6 · Ψ_global no es una media de Ψ(d): el símbolo está sobrecargado
La Tabla 1 rotula la fila agregada **"Global (simple mean)"** y reporta **0.349** en la columna Ψ. Pero la media simple de la columna Ψ es **0.329**, no 0.349. El 0.349 es el cociente de la Ec. (4), es decir una media de Ψ **ponderada por onto(d)**. Lo mismo en el control: media simple = 0.900, reportado = 0.905.

No es un error de cálculo — la Ec. (4) es la definición — pero la etiqueta induce a error y un lector cuidadoso hará la suma y creerá haber encontrado un fallo.

> **Corrección:** rotular la fila **"Global (Eq. 4, onto-weighted)"** y añadir al pie de tabla: *"Ψ_global is the onto-weighted mean of Ψ(d) per Eq. (4); the unweighted mean of the Ψ column is 0.329."* Considerar además usar **Ψ̄** o **Ψ_G** para distinguirlo tipográficamente de Ψ(d).

### H-7 · Redondeo inconsistente en la fila LegalTech
`75.5 × 0.67 = 50.59`, pero la tabla reporta `sds = 50.8`. El Ψ real es ≈ **0.673**. Es el único desvío >0.05 de la tabla.
> **Corrección:** reportar Ψ(LegalTech) = 0.67 con sds = 50.6, o bien Ψ = 0.673 con sds = 50.8. Coherencia a dos decimales en toda la columna.

### H-8 · "17 runs", "37 entradas de ledger", "cinco shadows regenerados" — tres conteos sin relación explicada
§4 usa tres cardinalidades distintas sin decir cómo se relacionan. El revisor preguntará: ¿por qué 37 entradas si hay 17 corridas? ¿Por qué solo 5 shadows si hay 17 corridas?
> **Corrección:** una frase: *"The 17 runs produced 5 full shadow regenerations (the remainder being integrity re-verifications); the ledger's 37 entries comprise runs, verifications and recorded methodological decisions."*

### H-9 · Estabilidad reportada solo para el índice declarativo, no para Ψ
Se afirma *"The index was stable across all five regenerated shadows"* — pero la métrica que el paper propone es Ψ, y no se reporta su variabilidad entre corridas.
> **Corrección:** añadir min–max o desviación de Ψ_global sobre los 5 shadows. Es la evidencia de **reproducibilidad del instrumento** y hoy falta. Si Ψ_global fue idéntico, decirlo explícitamente ("invariant across all five regenerations") es un resultado fuerte y gratuito.

### H-10 · El control sintético es un control positivo, no una validación de constructo
El texto dice que el control *"confirms that the low real coverage is a property of the observed ecosystem, not an artefact of the engine"*. Eso es correcto pero limitado: el control fue *"built to saturate the engine"* por los propios autores, así que demuestra ausencia de techo artificial (*ceiling effect*), no validez de medida.
> **Corrección:** reformular como *"a positive control ruling out a ceiling artefact in the scoring engine"* y trasladar la matización a Limitaciones. Baja el riesgo de un rechazo por sobre-interpretación, y no cuesta nada.

### H-11 · Colisión terminológica: "capas"
La arquitectura tiene **4 capas** (adquisición, semántica, validación, presentación); el shadow institucional tiene **7 capas arquitectónicas**. Mismo término, dos referentes, a tres páginas de distancia.
> **Corrección:** llamar a las primeras *"tiers"* o *"architectural layers of LegalShadow"* y a las segundas *"ecosystem layers of the observed institution"*.

### H-12 · Título vs. objeto de estudio
El título promete *"LegalTech Ecosystems"*; el paper observa el ecosistema digital **público de una institución judicial** (e-justicia / gobierno digital). "LegalTech" en la Tabla 1 es, además, solo **una de diez** dimensiones — lo que agrava la confusión de alcance.
> **Opción A (recomendada):** *"…for Semantic Validation of Judicial Digital Ecosystems"*.
> **Opción B:** mantener el título y añadir en la introducción una definición explícita de "LegalTech ecosystem" que abarque el caso judicial público.

---

## 5. Hallazgos menores y de estilo

| # | Ubicación | Problema | Sugerencia |
|---|---|---|---|
| m-1 | L.82 | *"To the best of our systematic comparison of the works reviewed above"* — agramatical | *"To the best of our knowledge, and based on a systematic comparison of the works reviewed above,"* |
| m-2 | L.153 | Párrafo *"In summary, this formalization transforms…"* — resumen redundante, tono promocional (*"rigorous foundation"*, *"bridges the gap"*) | Reducir a 1–2 frases o suprimir; el espacio se necesita para H-9 |
| m-3 | L.165 | El párrafo rotulado **"Semantic projection"** habla en realidad de la modularidad en 4 capas; el contenido real de proyección semántica está en L.167 | Mover ese texto al párrafo de arquitectura y dejar que **Semantic projection** encabece L.167 |
| m-4 | L.78 | Mezcla `-ize`/`-ise`: *"conceptualization"*, *"software artifacts"* junto a *"operationalised"*, *"artefact"* | Unificar en ortografía británica (el resto del paper lo es): *conceptualisation*, *artefacts* |
| m-5 | L.162 | El protocolo ético no menciona **robots.txt** ni intervalo entre peticiones | Añadir: *"…honours `robots.txt` directives and spaces requests by ≥N s"* — es lo primero que pregunta un revisor de ética de scraping |
| m-6 | L.70 | Keywords sin *semantic validation*, *digital governance*, *e-justice* | Añadir 2–3; mejora indexación |
| m-7 | L.68 | El **hallazgo reflexivo** (la institución carece del JSON-LD que el shadow usa para representarla) es el resultado más memorable y no está en el abstract | Añadir una frase final al abstract |
| m-8 | §1 | No hay una **pregunta de investigación** enunciada explícitamente | Una frase antes de C1–C3: *"RQ: to what extent does…"* |
| m-9 | L.68 | `\texorpdfstring` dentro de `\abstract{}` | Innecesario en el campo abstract de MDPI; simplificar para evitar sorpresas de compilación |
| m-10 | L.339 | *"Nothing in the architecture is country-specific"* — afirmación fuerte, no demostrada (validez externa = 1 institución) | Suavizar: *"Nothing in the architecture is country-specific by construction, though this remains to be demonstrated empirically."* |
| m-11 | Refs | 3 de 23 referencias son autocitas (13 %) y el párrafo L.78 es íntegramente autorreferencial | Porcentaje aceptable, pero conviene intercalar 1–2 trabajos de terceros en ese párrafo para que no lea como continuidad cerrada |
| m-12 | — | No se adjuntó `ICI2ST_LegalShadow_Ref.bib`; no pude verificar las 23 claves citadas | Verificar que las 23 claves existan y compilen sin `?` |

---

## 6. Alineación título ↔ abstract ↔ conclusiones (respuesta directa a la consulta)

**Está mayormente alineado.** El eje argumental es consistente de punta a punta:

> título (*validación semántica*) → abstract (*Ψ = 34.9 % vs. 46/100*) → §2 (*Ψ, δ formalizados*) → §4 (*Tabla 1, tres dimensiones en cero*) → §5 (*"declarative maturity is not machine-actionable governance"*).

Verificaciones puntuales de coherencia, todas **correctas**:

- Las 10 dimensiones listadas en el abstract = las 10 filas de la Tabla 1. ✓
- "Three dimensions have zero coverage" = ITIL, COBIT, DLT. ✓
- "34 components, 32 flows, 7 layers" = §4. ✓
- "17 dated runs / 187 requests / 170 snapshots / 0 mismatches" = §4. ✓
- "46/100 (Level 3)" = banda 41–60 de L. ✓
- Las conclusiones no introducen ningún claim ausente en resultados. ✓
- Las limitaciones cubren honestamente: superficie pública, σ sin panel independiente, media simple, validez externa, deriva de markup. ✓

**Los tres desajustes de alineación son:**

1. **Título** promete *LegalTech ecosystems*; el cuerpo entrega *un ecosistema judicial público* (H-12).
2. **Abstract** yuxtapone 46/100 y 34.9 % sin advertir que son 4 vs. 10 dimensiones (H-5). Es el desajuste más peligroso.
3. **Abstract** omite el hallazgo reflexivo, que las conclusiones elevan a resultado destacado (m-7).

---

## 7. Plan de corrección priorizado

**Antes de someter (bloqueantes)**

1. Rehacer la Figura 2b: añadir Seguridad, encender parcialmente TOGAF/AI/NIST/Seguridad, marcar el caption como esquemático — **H-1, H-2**
2. Desambiguar el barrido de sensibilidad con los números verificados — **H-3**
3. Reescribir `\dataavailability` con DOI de Zenodo y sin "on request" — **H-4**
4. Declarar "four-dimension" vs. "ten-dimension" en abstract y §4 — **H-5**
5. Re-rotular la fila global de la Tabla 1 y añadir el pie aclaratorio — **H-6**
6. Corregir el redondeo de LegalTech — **H-7**

**Fuertemente recomendado**

7. Conciliar 17 / 37 / 5 (**H-8**); reportar estabilidad de Ψ (**H-9**); reformular el control como control positivo (**H-10**); desambiguar "capas" (**H-11**); decidir el título (**H-12**)

**Oportunidad de valor**

8. La verificación numérica de §2 de este informe reprodujo **todo** el aparato desde la Tabla 1, incluido el barrido de sensibilidad. Ese es un nivel de reproducibilidad poco común. Añadir una frase en Conclusiones — *"every figure in Table 1 is recomputable from the published rubric and the dated JSON-LD shadows"* — convierte una fortaleza tácita en un argumento explícito de aceptación.

**Menores de estilo:** m-1 a m-12, aplicables en una pasada de edición.

---

## 8. Fortalezas a preservar (no tocar en la revisión)

- La **motivación de Ψ en tres pasos** (§2, "40 % for showing up, 60 % for the substance") es pedagógicamente excelente y rara en papers de ontologías.
- Las **propiedades declaradas de Ψ** — monotonía, cota superior inalcanzable por declaración, descomposición raíz/subconcepto — son exactamente las que un revisor pide de una métrica nueva, y están enunciadas y justificadas.
- El **hallazgo de que 50 vs. 51 estrellas producen coberturas que difieren por un factor de 2.6** es el mejor argumento del paper a favor de Ψ frente a un conteo ingenuo. Merece más espacio, no menos.
- La sección de **Limitaciones** es honesta y anticipa correctamente las objeciones (lower bound observable, σ sin panel, media simple, n = 1).
- El **encuadre shadow ≠ twin** justificado por competencia estatal es un argumento de diseño elegante y bien citado.
