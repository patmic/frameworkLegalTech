# Plan de ajustes — Reviewer 1, Round 1 · engproc-4523067

**Base:** `engproc-4523067 (V5).zip` → `ICI2ST_LegalShadow_Main.tex` (12 páginas, compila limpio).
**Estado:** nada ejecutado. Cada punto espera tu aprobación.
**Plazo:** ~3 de septiembre de 2026.

El revisor abre con *«thank you for inviting this high-quality research paper; it is very good»* y cierra con *«I am sure that after revision, the manuscript will be accepted»*. La distancia entre eso y lo que pide es corta: casi todo es estructura y presentación, nada toca el método ni las cifras.

---

## Resumen de los nueve pedidos

| # | Pedido | Tipo | Esfuerzo | Riesgo |
|---|---|---|---|---|
| R1 | Revisar el título | Ya hecho — solo explicar | 0 | — |
| R2 | Reescribir el abstract (objetivos, método, hallazgos, contribuciones) | Reescritura | 40 min | bajo |
| R3 | Introducción: quitar «subsecciones por párrafo» | Estructura | 30 min | bajo |
| R4 | Citar Cao et al. (cambio ambiental / derecho) | **Decisión editorial** | — | **ver §C** |
| R5 | `Related Work and Delimitation` → `Literature Review` | Renombrar + citas | 45 min | bajo |
| R6 | Citar Li et al. (Hainan) y Khaskheli et al. (refugiados) | **Decisión editorial** | — | **ver §C** |
| R7 | Figura 2 más legible + descripción de cada tabla | Presentación | 45 min | bajo |
| R8 | Separar Discussion de Conclusions | Estructura | 1 h | medio |
| R9 | Añadir Policy Implications, Future Research, Recommendations | Estructura | 1,5 h | **alto (páginas)** |

---

## A. Pedidos que ejecuto sin reservas

### A1 · Título (R1) — no requiere cambio, solo explicación
El revisor evaluó la versión del 9 de agosto, cuyo título era *«…Judicial Digital Ecosystems»*. **Ya lo cambiamos** a *«…LegalTech Ecosystems»* y el Academic Editor lo aprobó por escrito: *«The slight modification to the title to "LegalTech Ecosystems" is appropriate and has been noted»*.

*Propuesta:* mantenerlo y explicarlo en la carta. Si prefieres afinar más, la variante que añade alcance sería *«…for Semantic Validation of LegalTech Ecosystems: Evidence from a Judicial Institution»*, pero reabrir algo que el editor ya cerró tiene más coste que beneficio.

### A2 · Abstract (R2) — reescritura con los cuatro elementos
Hoy tiene **206 palabras** en un bloque continuo. MDPI pide **≤200** y el revisor pide que se vean explícitamente objetivos, metodología, hallazgos y contribuciones.

*Propuesta:* reescribirlo en cuatro movimientos identificables sin usar encabezados (MDPI no admite abstract estructurado en este formato): problema y **objetivo** → **método** (ontología de diez dimensiones, adquisición read-only, Ψ y δ) → **hallazgos** (46/100 frente a 34,9 %, tres dimensiones en cero, control 90,4 %) → **contribución** (arquitectura, protocolo auditable, métrica de cobertura). Objetivo: 195–200 palabras. Todas las cifras se conservan.

### A3 · Introducción (R3) — eliminar el efecto «subsección por párrafo»
Verifiqué el `.tex`: **la Introducción no tiene subsecciones**. Lo que el revisor ve es otra cosa, y tiene razón en que estorba:

1. Las contribuciones **(C1) (C2) (C3)** van con `\\` forzando salto de línea, así que se leen como tres mini-títulos.
2. Las secciones 4, 5 y 6 usan **doce encabezados en negrita a pie de párrafo** (`\textbf{Acquisition protocol.}`, `\textbf{Evidence corpus.}`, …). Al hojear, el paper entero parece subseccionado.

*Propuesta:* convertir C1–C3 en prosa corrida o en un `itemize` limpio, y reducir los encabezados de negrita de doce a cuatro o cinco, dejando solo los que marcan cambio real de tema.

### A4 · Literature Review (R5) — renombrar y completar citas
Renombrar `Related Work and Delimitation` → **`Literature Review`**, conservando la Tabla 1 de delimitación, que es lo que sostiene el claim de novedad ante el editor.

*Además:* el revisor dice que faltan citas en algunas afirmaciones. Haré una pasada localizando afirmaciones sin respaldo y añadiendo referencia donde exista. Te entrego la lista antes de tocar nada.

### A5 · Figura 2 y descripción de tablas (R7)
**Figura 2** es el listado JSON-LD en `verbatim` a `\footnotesize`. Propuesta: pasar a un entorno de listado con numeración de línea, cuerpo algo mayor y resaltado suave de las tres claves que importan (`maltg:evidence`, `maltg:mapsTo`, `maltg:gap`), que son las que sostienen el argumento de trazabilidad.

**Tablas:** la Tabla 1 hoy se despacha con una frase. Añadiré a ambas un párrafo introductorio que diga qué contiene, cómo leerla y qué conclusión soporta.

*(De paso arreglo el desborde de texto de la Figura 3(a) que te mostré: el borde corta «Class-driven read-only probe». Es un defecto objetivo que se publicaría así.)*

---

## B. Pedidos que requieren decisión de arquitectura

### B1 · Separar Discussion y Conclusions (R8)
Directo y razonable. §6 pasa a **§6 Discussion** (madurez declarativa vs. cobertura, hallazgo reflexivo, validez externa, limitaciones) y **§7 Conclusions** (síntesis de la contribución).

### B2 · Tres secciones nuevas (R9) — aquí está el riesgo real
Pide añadir **Policy Implications**, **Future Research Directions** y **Recommendations** después de la Conclusión.

El problema no es escribirlas, es que **ese contenido ya existe repartido**: la consecuencia prescriptiva del hallazgo reflexivo es policy implications; el cierre de conclusiones ya lista trabajo futuro; y las recomendaciones concretas (JSON-LD embebido, documentar APIs, manifiesto de gobernanza) ya están escritas. Si añado tres secciones sin redistribuir, el paper repite lo mismo tres veces — que es exactamente el defecto que corregimos hace dos rondas fusionando la Discusión de ocho párrafos a cinco.

**Propuesta:** *mover*, no duplicar. La parte prescriptiva sale del hallazgo reflexivo y se convierte en Policy Implications; las tres acciones concretas pasan a Recommendations dirigidas a instituciones judiciales; el trabajo futuro sale de Conclusions y se vuelve Future Research Directions. Estructura final:

> §6 Discussion · §7 Conclusions · §8 Policy Implications · §9 Future Research Directions · §10 Recommendations

**Coste:** el paper pasa de 12 a **14–15 páginas**. Recuerda que el Academic Editor elogió el «10-page format». Es la única tensión seria entre lo que pide el revisor y lo que valoró el editor.

---

## C. Las tres referencias sugeridas — decisión tuya

Verifiqué las tres. Existen y son reales:

| Referencia | Qué es | Relación con LegalShadow |
|---|---|---|
| **Cao et al. (2025)**, *Sustainability*, 12 citas | Riesgo del cambio ambiental global para la sostenibilidad económica y el derecho; tecnología digital y regulación | **Ninguna en sustancia.** Comparte solo el rótulo genérico «tecnología digital + gobernanza» |
| **Li et al. (2024)**, *Systems*, 12 citas | IA en innovación de servicios y **cumplimiento legal** en el Hainan Free Trade Port; riesgo legal de la IA, privacidad, sesgo algorítmico | **Parcial y defendible.** Toca cumplimiento legal y supervisión regulatoria de la IA, que conecta con la dimensión *AI integration* de la ontología |
| **Khaskheli et al. (2020)**, *ScienceRise: Juridical Science*, 4 citas | Migrantes ambientales, derecho internacional de refugiados, derechos humanos | **Ninguna.** No hay puente con sombras digitales, ontologías ni justicia electrónica |

Las tres juntas —derecho ambiental, IA empresarial en Hainan, derecho de refugiados— no forman un hilo con tu tema. El patrón se parece más a una solicitud de citación que a orientación bibliográfica.

**Y el propio correo de MDPI te ampara**, punto (IV):

> *«If the reviewer(s) recommended references, critically analyze them to ensure that their inclusion would enhance your manuscript. If you believe these references are unnecessary, you should not include them.»*

**Mi recomendación:** citar **Li et al.** en una frase honesta dentro de la dimensión de IA, y **declinar cortésmente** Cao y Khaskheli explicando el motivo en la carta. Añadir por tu cuenta **dos o tres referencias jurídicas genuinamente pertinentes** (justicia electrónica, informática jurídica), que es el pedido legítimo que hay detrás: *«cite legal references»*. Así respondes al fondo sin inflar la bibliografía.

Las alternativas son citarlas las tres (evita fricción, pero mete ruido que un lector notará) o declinar las tres (defendible, algo más áspero).

---

## D. Lo que entregaré cuando apruebes

1. `.tex` corregido con marcas `%>> R1-x` en cada cambio.
2. Los pasajes tocados en **azul** (`\textcolor{blue}`), como pediste para el punto (II) del correo, más una versión limpia para el PDF final.
3. PDF compilado y verificado.
4. ZIP para el campo *Manuscript* de SuSy.
5. Carta de respuesta punto por punto, incluida la justificación de las referencias que se declinen.
6. Texto para pegar en *Reply to editor*.
