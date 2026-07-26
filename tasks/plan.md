# Implementation Plan: Route Outlier ToC Pages (chapter_0 and chapter_N_extra_1)

## Overview
Refactor `group_pages_by_toc` in `parser.py` so pages falling outside defined `toc.json` chapter boundaries are routed cleanly:
1. Pages before Chapter 1 (`page_index < first_chapter.start_page`) are grouped into `c000` (`chapter_0`).
2. Gap pages between intermediate chapters are merged into the preceding chapter.
3. Trailing pages after the last chapter (`page_index > last_chapter.end_page`) are placed into an extra chapter folder derived from the last chapter ID (e.g., `c010x1` -> `chapter_10_extra_1`).

## Architecture Decisions
- **`c000` for Front Matter**: Front matter / cover pages before page 1 are mapped to `c000`, which formats to `chapter_0`.
- **`c{last}x1` for Trailing Pages**: Trailing pages past the last chapter's `end_page` receive an incremented extra ID based on the last chapter's ID (`c{num}x{extra+1}`).
- **Intermediate Gap Handling**: Gap pages between chapter ranges are assigned to the preceding chapter.

## Task List

### Phase 1: Outlier Page Routing Logic
- [ ] Task 1: Update `group_pages_by_toc` in `parser.py` with `c000` front-matter routing, intermediate gap assignment, and `c{last}x1` trailing extra routing.

### Phase 2: Unit Testing & Verification
- [ ] Task 2: Add comprehensive unit tests in `tests/test_parser.py` covering front-matter pages (`chapter_0`), intermediate gap pages, and trailing pages (`chapter_N_extra_1`).
- [ ] Task 3: Execute test suite (`python -m unittest discover -s tests`) and confirm 100% pass rate.

### Checkpoint: Complete
- [ ] All unit tests pass cleanly.
