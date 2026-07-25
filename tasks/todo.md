# Todo Checklist: Table of Contents Support

- [x] **Task 1**: Implement `load_toc_data` helper in `parser.py` (reads internal zip `toc.json` or external `[stem].toc.json`).
- [x] **Task 2**: Implement `group_pages_by_toc` helper to slice image pages using `start_page` and `end_page` bounds.
- [x] **Task 3**: Update `process_single_book` to check for `toc.json` and use `toc.json` grouping with fallback to regex matching.
- [x] **Task 4**: Ensure `toc.json` file is saved to `output/local/[BookName]/toc.json`.
- [x] **Task 5**: Add unit test coverage in `tests/test_parser.py` for embedded `toc.json`, external `toc.json`, missing `toc.json`, and malformed JSON fallback.
- [x] **Task 6**: Execute test suite (`python -m unittest discover -s tests`) and confirm 100% pass.
