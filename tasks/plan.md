# Implementation Plan: Add ZIP File Support

## Overview
Enhance `parser.py` to support `.zip` comic books alongside `.cbr` and `.cbz` files. Support simple numerical image filenames (`1.jpg`, `2.jpg`, ..., `23.jpg`), filter out non-image files, select the first sorted image as `cover.jpg` when no explicit cover tag exists, and place single-chapter images into `chapter_1`.

## Architecture Decisions
- Extend `extract_page_info` with a regex digit extraction fallback on filename stems.
- Use `c001` as the default chapter ID when no chapter tag is present, placing images into `chapter_1`.
- Update cover selection to fall back to the first naturally sorted image across all chapters.
- Expand file scanning filter in `process_books` to include `.zip` extensions.

## Task List

### Phase 1: Core Implementation
- [ ] Task 1: Update `parser.py` logic to support `.zip` extension, digit fallback for `extract_page_info`, `c001` default chapter, and natural cover fallback.

### Phase 2: Testing & Verification
- [ ] Task 2: Add comprehensive unit tests in `tests/test_parser.py` for `.zip` parsing, plain numerical page ordering, non-image file filtering, and automatic cover generation.
- [ ] Task 3: Run unittest suite and verify 100% test pass rate.

## Verification
- [ ] Automated tests pass: `python -m unittest discover -s tests`
