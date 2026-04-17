# claw test suite

Pytest suite for the `claw` CLI. Uses Click's `CliRunner` — every test runs in-process.

## Run

```bash
# From scripts/claw/
pytest                      # full suite
pytest -n auto              # parallel (requires pytest-xdist)
pytest -m 'not external_tool'  # fast-only; skips pandoc/ffmpeg/etc. tests
pytest --no-network         # skip network-tagged tests
pytest tests/test_help.py -v
```

## Layout

- `conftest.py` — shared fixtures (`sample_csv`, `sample_xlsx`, `sample_pdf`,
  `sample_png`, `sample_html`, `sample_xml`, `sample_md`, `sample_pptx`,
  `sample_docx`, `sample_mp4`, `sample_json_rows`) and `skip_without(tool)`.
- `test_common.py` — direct unit tests for `claw.common` helpers
  (PageSelector, RangeSelector, NodeSelector, Geometry, safe_write).
- `test_help.py` — every `--help` for every noun and verb exits 0 with
  non-empty output.
- `test_happy_path.py` — one test per verb, minimal required flags,
  synthesized fixtures, `tmp_path` for all I/O.
- `test_flag_combinations.py` — parametrized flag-combo coverage for the 20+
  highest-value verbs.
- `test_error_contracts.py` — exit codes, error JSON shape, overwrite
  protection, mkdir contract.

## External-tool gating

Tests that need `pandoc`, `ffmpeg`, `ffprobe`, `tesseract`, `magick`, `qpdf`,
or `gws` call `skip_without("<tool>")` and skip cleanly when the tool is
absent from `PATH`.

## No real external APIs

Tests never reach Gmail, Drive, Docs, or launch a browser. For those verbs,
we use `--dry-run` or `--help` only.
