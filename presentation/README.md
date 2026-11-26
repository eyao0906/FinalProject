# STAT 906 presentation draft

`Presentation.qmd` is the editable source for the 12-slide timed Beamer deck and its three explicitly marked backup slides. `Presentation.pdf` is the rendered draft. `slide_notes.md` has brief speaking cues and timings; `source_trace.md` maps displayed values and figures back to saved records.

## Reproducible render

From the repository root in PowerShell, after Quarto and a LaTeX distribution are installed:

```powershell
quarto render presentation\Presentation.qmd --to beamer
```

Quarto writes `presentation\Presentation.pdf`. The PNG assets are committed alongside the source, so rendering the deck does not require rerunning experiments.

To regenerate the presentation-specific figures from saved CSV data:

```powershell
py -3.14 presentation\build_assets.py
```

This only writes PNGs under `presentation\assets`; it does not alter `results\`. Python needs the existing project dependencies from `pyproject.toml` (pandas and matplotlib). The backup correction figure is included directly from the saved core results.
