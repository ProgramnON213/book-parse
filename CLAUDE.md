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
1. **Archive Type**: CBR files in this project are zip files renamed to `.cbr` containing webp images. Use the built-in `zipfile` module. Do not require native `unrar` libraries.
2. **Page Formats**: Extract page webp files directly without transcoding. Only convert the cover image page to JPEG format (`cover.jpg`).
3. **Chapter Folder Formatting**:
   - Chapter IDs are of the form `c\d+(?:x\d+)?` (e.g. `c001`, `c005x1`).
   - Standard chapters: `chapter_[number]` (e.g., `chapter_1`).
   - Extra chapters: `chapter_[number]_extra_[suffix]` (e.g., `chapter_5_extra_1`).
4. **Natural Sorting**: Sort chapters using natural tuple sorting `(chapter_num, extra_num)`. Pages are sorted numerically by their starting page prefix (e.g., `p001`).

### Typing & Code Style
- Use strict typing annotations (e.g., `List`, `Dict`, `Tuple`, `Any` from `typing`).
- Maintain standard PEP 8 naming conventions.
- Keep helper functions simple and focused.
- All code logic must be covered by unit tests in `tests/test_parser.py`.
