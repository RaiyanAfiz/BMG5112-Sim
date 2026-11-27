# BMG5112-Sim: web version

The Hill-type muscle contraction simulator from `main`, rewritten in plain HTML, CSS and JavaScript so it can run on GitHub Pages. There is no build step and nothing to install.

## Run it locally
Double-click `index.html`, or serve the folder (for example `python -m http.server`) and open http://localhost:8000.

## Publish on GitHub Pages
1. Push this branch: `git push -u origin gh-pages`
2. On GitHub, go to **Settings → Pages**.
3. Under **Build and deployment**, set **Source** to *Deploy from a branch*, then pick **gh-pages** and **/ (root)**, and click **Save**.

The site appears at `https://<owner>.github.io/BMG5112-Sim/` after a minute or two.

> GitHub Pages on a **private** repository needs a paid GitHub plan (Pro, Team or Enterprise). On a free plan the repository has to be public.

## Files
| File | Ported from | What it does |
|---|---|---|
| `index.html`, `css/style.css` | `app.py` (layout) | Page layout, controls, light/dark theme |
| `js/model.js` | `model.py` | Hill model and the muscle-condition presets |
| `js/app.js` | `app.py` | Connects the controls to the model and the graphics |
| `js/fv-plot.js` | `visualizer.py` (`MuscleVisualizer`) | Force-velocity curve, power overlay, operating point |
| `js/sarcomere.js` | `visualizer.py` (`_draw_sarcomere`, `_draw_myosin_heads`) | Sarcomere schematic and myosin heads |
| `js/arm.js` | `visualizer.py` (`ArmVisualizer`) | Whole-muscle (elbow flexor) view |
| `js/draw.js` | (new) | Shared canvas helpers |

The numbers and graphics match the Python version. The myosin-head binding thresholds are copied from the Python app's `np.random.default_rng(42)` draw, so the same heads are bound in both versions. If the model or graphics change on `main`, the matching file here needs the same change.
