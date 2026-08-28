# Plan de ajustes — Ronda 2 · engproc-4523067

**Base de trabajo:** `engproc-4523067.zip` → `ICI2ST_LegalShadow_Main.tex` (18 ago 2026, 12 páginas).
Verificado: compila limpio (0 overfull, 0 referencias indefinidas) y **ya contiene** todas las correcciones de la ronda anterior.

**Estado:** ningún cambio ejecutado. Cada punto espera tu aprobación.

---

## 1. Qué dice realmente el sistema

Hay que separar dos cosas que en SuSy aparecen juntas y significan lo contrario:

**Lo que ya está resuelto.** El Academic Editor (Editor 1, *Editorial Pre-Check*) respondió confirmando que se atendieron todos los puntos mayores y menores: la validez externa y el protocolo de 4 pasos, la transparencia de Γ respaldada por los artefactos abiertos, la delimitación de novedad en la Sección 2 y la Tabla 1, el contraste como *"difference of frame"* en la Sección 5, y las limitaciones y recomendaciones de política en la Sección 6. Añade que el cambio de título a *LegalTech Ecosystems* «is appropriate and has been noted» y cierra con «methodologically sound, transparent, and ready for publication».

**Lo que sigue abierto.** Son tres cosas, y solo una exige tocar el paper:

| # | Pendiente | Dónde | Acción |
|---|---|---|---|
| A | `Pending Reply` al Academic Editor | *Reply to Academic Editors* → botón **Reply to editor** | Responder (§4 de este plan) |
| B | Subir la versión revisada | *Upload Revised Manuscript* | Subir ZIP + PDF + cover letter |
| C | **Reviewer 1, Round 1 — «Figures and tables can be improved»** | *English Language and Figures → Quality of Figures* | Ajustes técnicos (§3) |

**Plazo:** el correo del 24 de agosto da 10 días → **~3 de septiembre de 2026**. Hoy es 27 de agosto: quedan 7 días.

---

## 2. Lo que me falta para cerrar el plan

Los documentos que enviaste contienen la **valoración resumida** de Reviewer 1 (`Figures and tables can be improved`), pero **no su informe completo**. El correo dice que está en:

> `https://susy.mdpi.com/user/manuscripts/resubmit/db84fb99dab0da92393e8cb12144936f`

y en SuSy detrás del enlace **Peer Review Reports**.

Sin ese informe no sé si Reviewer 1 señaló figuras concretas, pidió algo específico (resolución, color, leyendas, datos numéricos en las tablas) o solo marcó la casilla genérica. **El plan de abajo cubre los defectos que yo mismo verifiqué sobre el PDF**, pero puede quedarse corto o sobrar respecto de lo que él pidió.

> **Acción necesaria:** descarga el informe de Reviewer 1 y pásamelo antes de ejecutar. Si solo marcó la casilla sin comentario textual, dímelo y ejecutamos este plan tal cual.

---

## 3. Ajustes propuestos — aprobar punto por punto

Cada punto indica el defecto **verificado sobre el PDF enviado**, el arreglo, el riesgo y el esfuerzo.

### Bloque A — Defectos objetivos (recomiendo aprobar los tres)

**A1 · Figura 3(a): el texto se desborda de las cajas.**
En «Class-driven read-only probe» y «Ontology Ω + target URL» el borde redondeado **corta el texto** por ambos lados, y las puntas de flecha se solapan con los bordes. Es el defecto más visible del paper y el candidato más probable a haber disparado el comentario del revisor.
*Arreglo:* ampliar `minimum width` de 1.66 a ~1.95 cm, subir la separación entre nodos de 1.90 a 2.15 cm, y añadir `inner xsep` para que el texto respire. La figura crece ~1 cm de ancho, que hay disponible.
*Riesgo:* bajo. *Esfuerzo:* 10 min. *Impacto en páginas:* ninguno.

**A2 · Figura 3(b): etiquetas ilegibles.**
Las etiquetas de constelación están en `\tiny` dentro de un `scope` con `scale=0.80` → **≈4 pt efectivos**. La mayoría de editoriales, MDPI incluida, considera el mínimo aceptable ~6 pt. Además la esfera ocupa poco más de la mitad del ancho útil mientras las etiquetas van apretadas.
*Arreglo:* subir a `\scriptsize`, escala a 0.95, radio de etiqueta a 2.9, y separar las dos líneas de cada etiqueta. Aprovecha el margen lateral que hoy está vacío.
*Riesgo:* medio — puede provocar *overfull* si se pasa del ancho; se verifica al compilar. *Esfuerzo:* 20 min.

**A3 · Figura 4: gráfico comprimido.**
4,0 cm de alto para 10 categorías deja las barras finas, las etiquetas rotadas rozan el marco y la línea δ se confunde con las barras.
*Arreglo:* altura a 5,2 cm, `bar width` de 5 a 6 pt, marcadores de la serie δ más visibles y `enlarge x limits` para despegar las etiquetas del marco.
*Riesgo:* bajo, pero **suma ~0,4 página**. *Esfuerzo:* 10 min.

### Bloque B — Coherencia visual (recomiendo aprobar B1)

**B1 · Unificar la codificación «evidenciado / no evidenciado».**
La Figura 1 usa **rectángulos grises**; la Figura 3 usa **círculos ámbar** para exactamente el mismo concepto. Un revisor de figuras lo lee como inconsistencia. Además, en la Figura 1 los subconceptos adyacentes casi se tocan (0,06 cm) y sus bordes discontinuos se funden en una tira continua.
*Arreglo:* llevar la Figura 1 a la paleta ámbar/hueco de la Figura 3 y separar las cajas a 0,66 cm.
*Riesgo:* bajo. *Esfuerzo:* 15 min.

**B2 · Etiquetas de panel en la Figura 1.**
La Figura 3 tiene (**a**)/(**b**); la Figura 1 no tiene ninguna pese a mostrar tres paneles.
*Arreglo:* añadir (**a**)(**b**)(**c**) y referenciarlos en el pie.
*Riesgo:* ninguno. *Esfuerzo:* 5 min.

### Bloque C — Opcionales (mi recomendación: solo si Reviewer 1 lo pide)

**C1 · Figura 2 → «Listing 1».**
Es un bloque de código numerado como figura. Algunos revisores prefieren un entorno de listado propio. *Contra:* renumera todas las figuras posteriores y las referencias cruzadas.

**C2 · Nota al pie en la Tabla 2.**
Añadir una línea explicando `Ψ ctrl` dentro de la tabla en lugar de solo en el pie.

**C3 · Verificación en escala de grises.**
Generar las figuras en gris para comprobar que ámbar-lleno vs. hueco sigue distinguiéndose impreso en blanco y negro.

### Lo que NO propongo tocar

El contenido científico, la estructura de secciones, las cifras, la bibliografía y el título. El editor los dio por buenos de forma explícita; abrirlos ahora solo añade riesgo.

---

## 4. Cómo responder en SuSy

Son **dos pantallas distintas**, en este orden.

### Paso 1 — Responder al Academic Editor

*Reply to Academic Editors* → fila con estado **Pending Reply** → botón **Reply to editor**. Es una caja de texto. Texto sugerido:

> Dear Academic Editor,
>
> Thank you for your assessment and for confirming that the concerns raised at pre-check have been addressed, including the note on the revised title.
>
> We have now also attended to the point raised by Reviewer 1 under *Quality of Figures*. In the version submitted with this reply we have improved the legibility and internal consistency of the figures: text that overflowed its containers in Figure 3(a) has been corrected, the labels in Figure 3(b) have been enlarged to a legible size, Figure 4 has been given room enough for its ten categories, and Figures 1 and 3 now share a single visual encoding for evidenced and unobserved concepts. No scientific content, numerical result or claim has changed.
>
> We remain at your disposal for any further clarification.
>
> Yours sincerely,
> Patricio M. Paccha-Angamarca, on behalf of all authors

*(Ajustar la lista si apruebas solo parte de los bloques.)*

### Paso 2 — Subir la versión revisada

*Upload Revised Manuscript*. Campos:

| Campo | Qué subir |
|---|---|
| **Manuscript (Word/ZIP/RAR)** ★ obligatorio | ZIP con `.tex` + `.bib` (+ figuras si las hubiera externas) |
| **Manuscript (PDF Version)** | PDF compilado de esa misma fuente |
| Supplementary File(s) | vacío |
| Figures, Graphics, Images | vacío — las figuras son TikZ, van dentro del `.tex` |
| Graphical Abstract | vacío |
| Non-published Material | vacío |
| **Cover Letter (PDF)** ★ obligatorio | carta punto por punto (§5) |
| **Authorship Changed?** ★ | **No** |

### Punto (II) del correo: marcar los cambios

El correo pide explícitamente: *«Highlight any revisions to the manuscript, so editors and reviewers can see any changes made.»* Con LaTeX hay dos formas:

1. **Color en el texto** — envolver los pasajes tocados en `\textcolor{blue}{...}`. Simple y visible, pero ensucia el PDF final y hay que revertirlo después.
2. **`latexdiff`** entre la versión enviada y la nueva, y subir ese PDF marcado como *Supplementary File*. Más limpio y es lo que esperan los editores de MDPI.

Como esta ronda solo toca figuras, propongo la opción 2 más una frase en la carta diciendo que los cambios se limitan a los entornos `tikzpicture` y `axis`. Dime si la prefieres.

---

## 5. Documentos que prepararé cuando apruebes

1. `ICI2ST_LegalShadow_Main.tex` corregido, con marcas `%>> R1` en cada cambio.
2. PDF compilado y verificado (0 overfull, 0 referencias indefinidas).
3. ZIP listo para el campo *Manuscript*.
4. Cover letter en LaTeX + PDF, punto por punto sobre lo de Reviewer 1.
5. PDF de `latexdiff` si eliges esa opción.
6. Texto plano para pegar en *Reply to editor*.

---

## 6. Riesgo que quiero dejar por escrito

El Academic Editor escribió literalmente:

> «[Optional: It will be sent back to the original reviewer for a final quick confirmation / OR: It is recommended for acceptance in its current form]»

Ese corchete es **una plantilla que quedó sin editar**. Significa que la ruta final —volver a Reviewer 1 o ir directo a aceptación— no está decidida en el texto que recibiste. No es motivo para cuestionar nada, pero sí para no asumir que el paper ya está aceptado: la observación de figuras sigue viva y conviene atenderla antes de subir.
