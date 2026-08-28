# Paquete LaTeX — Tesis MALTG (formato UPS)

**Contenido**
- `tesis_MALTG.tex` — documento completo según la plantilla doctoral UPS (book, 12pt, márgenes y portada de la plantilla): Resumen/Abstract, Cap. 1–5, 2 algoritmos, 8 tablas, 6 figuras y Apéndice A de reproducción.
- `Bibliografia_MALTG.bib` — 22 referencias de revistas especializadas (estilo `ieeetr`, citas numéricas).
- `Figuras/*.png` — generadas desde los DATOS REALES de la app (corte 2026-07): MAPE-K, dimensiones declarado-vs-medido, índice por procedimiento, dispersión IVF–IDP, tornado de sensibilidad, matriz de confusión (sesión simulada, semilla 42).
- `escudoUPS.png` — de la plantilla original.
- `tesis_MALTG_preview.pdf` — compilación de verificación (44 págs.) hecha SIN babel-spanish ni algorithms (no disponibles en el entorno de prueba); en tu TeX Live completo compila con el preámbulo fiel a la plantilla.

**Compilar (en tu equipo, con TeX Live completo):**
```
pdflatex tesis_MALTG.tex
bibtex   tesis_MALTG
pdflatex tesis_MALTG.tex
pdflatex tesis_MALTG.tex
```

**Regenerar las cifras/figuras** (reproducibilidad): ejecutar los endpoints del Apéndice A (Tabla de reproducción) con la app levantada (`docker compose up`) y volver a correr el script de figuras. Los valores del documento corresponden a `contexto_adaptacion` del corte indicado; congélalos junto con `salud_global_cache.json` al depositar.
