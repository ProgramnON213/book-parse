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
python parser.py --source ./source --output ./output
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

### Typing & Code Style
- Use strict typing annotations (e.g., `List`, `Dict`, `Tuple`, `Any` from `typing`).
- Maintain standard PEP 8 naming conventions.
- Keep helper functions simple and focused.
- All code logic must be covered by unit tests in `tests/test_parser.py`.
