# Task List

- [x] Task 1: Add `load_meta_data` and `transform_meta_to_details` in `parser.py`
  - Acceptance: `load_meta_data` extracts internal & external `meta.json`. `transform_meta_to_details` converts `n20` schema into `details.json` dictionary.
  - Verify: Unit test `load_meta_data` and `transform_meta_to_details`.
  - Files: `parser.py`

- [x] Task 2: Integrate `meta.json` handling into `process_single_book`, `process_books`, and CLI args
  - Acceptance: `process_single_book` writes `details.json` to `output/local/[BookName]/details.json` if `meta.json` exists, or proceeds normally without `details.json` if absent. `--meta` CLI option added (default `"n20"`).
  - Verify: Run test suite.
  - Files: `parser.py`, `CLAUDE.md`

- [x] Task 3: Add unit tests for `meta.json` parsing and CLI options
  - Acceptance: `python -m unittest discover -s tests` passes 100%.
  - Verify: `python -m unittest discover -s tests`
  - Files: `tests/test_parser.py`
