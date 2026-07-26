# Todo Checklist: Non-cXXXX Chapter Auto-Numbering & Strict Extra Slicing

- [x] **Task 1**: Update `group_pages_by_toc` in `parser.py` to auto-number non-`cXXXX` chapter IDs sequentially and strictly isolate non-TOC pages into extra folders.
- [x] **Task 2**: Add `test_group_pages_by_toc_named_sections` in `tests/test_parser.py` for named sections (`finale`, `appendix`) following `c006`.
- [x] **Task 3**: Execute test suite (`python -m unittest discover -s tests`) and confirm 100% pass rate.
