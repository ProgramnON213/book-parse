# Implementation Plan: Add Table of Contents (toc.json) Support

## Overview
Enhance `parser.py` in `book-parse` to detect and parse `toc.json` (either embedded within comic archives or placed alongside archive files in the source directory). When present, `toc.json` chapter page ranges (`start_page` to `end_page`) will dictate how pages are grouped into chapter directories. `toc.json` will also be copied into the output book folder (`output/local/[BookName]/toc.json`). Fallback to existing regex-based chapter parsing remains active when `toc.json` is absent or unparseable.

## Architecture Decisions
- **`toc.json` Resolution Order**:
  1. Check inside zip archive for `toc.json` (case-insensitive filename match).
  2. Check source directory for `[archive_stem].toc.json` or `toc.json`.
- **Page Grouping Logic**:
  - Sort all valid image pages naturally into 1-indexed order (1 to N).
  - Map `start_page` and `end_page` from `toc.json` entries to page position indices (or extracted page numbers).
  - Group matching pages into chapter folders using `format_chapter_folder_name(chap["id"])` (e.g. `c001` -> `chapter_1`).
  - Fall back to standard regex parsing if `toc.json` is absent/invalid.
- **Output Preservation**:
  - Save/copy `toc.json` to `output/local/[book_folder]/toc.json`.

## Task List

### Phase 1: Foundation & Helper Functions
- [ ] Task 1: Add `toc.json` loader helper (`load_toc_data`) in `parser.py` supporting internal zip reading and external file fallback.
- [ ] Task 2: Implement page-range grouping logic (`group_pages_by_toc`) based on `start_page` and `end_page` boundaries.

### Checkpoint: Foundation
- [ ] Helper functions pass isolated unit tests.

### Phase 2: Parser Integration
- [ ] Task 3: Integrate `toc.json` parsing into `process_single_book` in `parser.py`.
- [ ] Task 4: Ensure `toc.json` is copied/written to the destination book folder in `output/local/[book_folder]/toc.json`.

### Checkpoint: Core Integration
- [ ] End-to-end processing works for books with embedded or external `toc.json`.

### Phase 3: Unit Testing & Verification
- [ ] Task 5: Add comprehensive unit tests in `tests/test_parser.py` covering embedded `toc.json`, external `toc.json`, missing `toc.json`, and malformed JSON fallback.
- [ ] Task 6: Run full unit test suite and verify 100% pass rate.

### Checkpoint: Complete
- [ ] All unit tests pass cleanly.

## Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Malformed `toc.json` crashes parsing | High | Wrap JSON parsing in try/except block; log warning and fall back to regex parsing |
| Pages outside defined `toc.json` ranges | Med | Assign remaining/unmatched pages prior to first chapter or past last chapter into appropriate fallback chapter (e.g., `chapter_1`) |
