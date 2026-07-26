# Todo Checklist: Outlier Page Routing (chapter_0 & extra chapters)

- [x] **Task 1**: Update `group_pages_by_toc` in `parser.py` to route leading pages (`i < first_start`) to `c000` (`chapter_0`), intermediate gap pages to preceding chapter, and trailing pages (`i > last_end`) to `c{last}x1` (`chapter_N_extra_1`).
- [x] **Task 2**: Add unit tests in `tests/test_parser.py` for `chapter_0` front matter, intermediate gap pages, and trailing `chapter_N_extra_1` pages.
- [x] **Task 3**: Execute test suite (`python -m unittest discover -s tests`) and confirm 100% pass rate.
