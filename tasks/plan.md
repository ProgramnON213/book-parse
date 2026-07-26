# Implementation Plan: Non-cXXXX Chapter Auto-Numbering & Strict Non-TOC Extra Slicing

## Overview
Update `group_pages_by_toc` in `parser.py` to:
1. Sequentially resolve non-`cXXXX` chapter IDs in `toc.json` (such as `finale`, `appendix`, `afterword`, `ch1`, or missing IDs) into continuous numeric chapter IDs (`c007` -> `chapter_7`, `c008` -> `chapter_8`), continuing from the highest numeric chapter ID.
2. Strictly isolate images not covered by explicit `[start_page, end_page]` ranges in `toc.json` into extra folders (`chapter_0` for leading pages, `chapter_N_extra_1` for gap and trailing pages).

## Architecture Decisions
- **Monotonic Chapter ID Resolution**:
  - Maintain a running `current_chap_num` counter.
  - Preserved IDs: `c001` .. `c006` update `current_chap_num = 6`.
  - Non-`cXXXX` IDs: `current_chap_num += 1`, assigning `f"c{current_chap_num:03d}"` (`c007`, `c008`, etc.).
- **Strict Range Isolation**:
  - Pages inside `[start_page, end_page]` belong to `chapter_[N]`.
  - Leading pages (`i < first_start`): `c000` -> `chapter_0`.
  - Intermediate gap pages & trailing pages: `c{N}x1` -> `chapter_N_extra_1`.

## Task List

### Phase 1: Implementation
- [ ] Task 1: Update `group_pages_by_toc` in `parser.py` to auto-number non-`cXXXX` chapter entries and strictly isolate non-TOC pages into extra folders.

### Phase 2: Unit Testing & Verification
- [ ] Task 2: Add unit test `test_group_pages_by_toc_named_sections` in `tests/test_parser.py` covering named sections (`finale`, `appendix`) after `c006`, verifying `chapter_7`, `chapter_8` generation.
- [ ] Task 3: Execute test suite (`python -m unittest discover -s tests`) and confirm 100% pass rate.

### Checkpoint: Complete
- [ ] All unit tests pass cleanly.
