# CLAUDE.md - Developer and Coding Agent Guide

This file outlines the build, test, and style conventions for the CBR Book Parser codebase, assisting future coding agents.

## Commands

### Dependencies
Setup environment:
```bash
pip install Pillow
```

### Running the Parser
Run the parsing script:
```bash
python parser.py --source ./source --output ./output --archive ./archive
```

### Running Tests
Execute unit and integration tests:
```bash
python -m unittest discover -s tests
```

---

## Code & Testing Conventions

### Project Constraints
1. **Archive Type**: CBR, CBZ, and ZIP files in this project are zip archives (using `.cbr`, `.cbz`, or `.zip` extensions) containing image files. Use the built-in `zipfile` module. Do not require native `unrar` libraries. Non-image files (`.txt`, `.nfo`), hidden files (`.DS_Store`), and `__MACOSX` directories are ignored.
2. **Page Formats & Filenames**: Extract page files directly without transcoding, preserving their original format and extension (supporting `.webp`, `.jpg`, `.jpeg`, `.png`). Only convert the cover image page to JPEG format (`cover.jpg`). Supports both `p001` tagged pages and plain numerical filenames (e.g. `1.jpg`, `2.jpg`).
3. **Chapter Folder Formatting**:
   - Chapter IDs are of the form `c\d+(?:x\d+)?` (e.g. `c001`, `c005x1`). Files without chapter tags default to `chapter_1`.
   - Standard chapters: `chapter_[number]` (e.g., `chapter_1`).
   - Extra chapters: `chapter_[number]_extra_[suffix]` (e.g., `chapter_5_extra_1`).
4. **Natural Sorting & Covers**: Sort chapters using natural tuple sorting `(chapter_num, extra_num)`. Pages are sorted numerically by page index/filename stem. If no explicit `[Cover]` or `p000` tag exists, automatically use the first naturally sorted image as `cover.jpg`.
5. **Source Archiving & Collisions**: Successfully parsed archive files in `--source` are automatically moved to `--archive` (default `./archive`). If a file with the same name already exists in the archive folder, a `_YYYYMMDD_HHMMSS` timestamp suffix is appended to prevent data loss. Corrupted or unparseable files remain in `--source`.
6. **Table of Contents Support**: If `toc.json` is present inside the archive or alongside in `--source` (`[stem].toc.json`), chapter page ranges (`start_page` to `end_page`) determine chapter slicing, and `toc.json` is saved to `output/local/[BookName]/toc.json`. Defaults to regex parsing if `toc.json` is missing or invalid.
7. **Security & Path Safety**: Use `_safe_join` for all destination path resolution to strictly prevent directory traversal. Folder names are sanitized against Windows reserved names (`CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`) and trailing dots/spaces. Reading `toc.json` (internal and external) is subject to `MAX_FILE_SIZE` bounds checking. Sort keys and chapter formatting are cached with `@lru_cache`.

### Typing & Code Style
- Use strict typing annotations (e.g., `List`, `Dict`, `Tuple`, `Any` from `typing`).
- Maintain standard PEP 8 naming conventions.
- Keep helper functions simple and focused.
- All code logic must be covered by unit tests in `tests/test_parser.py`.
