# Guía de Anotación — Gold Standard del Razonador COGEP (1 página)

**Objetivo.** Crear el estándar de referencia para medir la validez del mapeo providencia→acto y de los dictámenes de término.

**Unidad de anotación.** Cada actuación (providencia) de una causa seleccionada.

**Qué anotar por actuación (en el panel Validez IA del tab Adaptativo):**
1. **Acto procesal correcto**: seleccione el acto de la ontología COGEP al que corresponde la actuación (p.ej. CALIFICACIÓN DE DEMANDA → act_calificacion). Si no corresponde a ninguno, elija "ninguno / fuera de frontera".
2. **Veredicto correcto** (solo si la actuación cierra un término legal): CUMPLE / ALERTA / INCUMPLE según su cómputo manual de días hábiles (Art. 73 y 77 COGEP), o NO_EVALUABLE.
3. **Notas**: ambigüedades, providencias mixtas, fechas dudosas.

**Criterios:**
- Anote según el CONTENIDO de la providencia, no según el nombre que le dio el sistema.
- Días hábiles: excluya sábados, domingos, feriados nacionales y suspensiones del CJ (el calendario vigente está en el panel Calendario).
- En caso de duda entre dos actos, elija el que produce efectos procesales (p.ej. auto que califica Y ordena citación → act_calificacion) y déjelo en notas.
- No consulte la predicción del sistema antes de decidir (se muestra solo como referencia gris después de anotar).

**Estratificación mínima sugerida:** 30–50 actuaciones cubriendo SUMARIO, MONITORIO y (si hay) EJECUCIÓN/APELACIÓN, de ≥8 causas distintas.

**Doble anotación (deseable):** un segundo abogado anota 15–20 actuaciones ya anotadas por el primero; el sistema calcula kappa de Cohen automáticamente.
