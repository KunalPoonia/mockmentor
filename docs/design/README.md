# Design archive

Historical design references, kept for provenance. **Nothing here is used by
the running app** — the live UI is `UI/index.html` (served by `src/server.py`),
which uses only `UI/animated_background/white.mp4`.

- `mockups/` — the original Stitch mockups (`code.html` + `screen.png`) for each
  screen. These were merged by hand into the single-page `UI/index.html`.
  - `subject_selector/`, `grading_state/`, `active_question/`, `verdict_source/`
- `liquid_glass.md` — notes on the liquid-glass visual design system.
- `animated_background.md` — notes on the WebGL/video background.
- `animated_background_shader.html` — standalone demo of the rotating-light shader.
- `black_background.mp4` — the dark background variant (the app ships the white one).
