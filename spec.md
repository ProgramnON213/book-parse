# Spec: CBR Book Parser

## Objective
The program will parse a set of `.cbr` (renamed `.zip` archives containing webp images) files in a source directory, group pages by chapter, and organize them into a clean series directory structure with a dedicated cover image and chapter-based subfolders.

Specifically, it will take files from:
`source/*.cbr`

And output the following structure to a target storage directory:
```
[storage_location]/local/
└── [the series title]/
    ├── cover.jpg
    ├── chapter_1/
    │   ├── image_1.webp
    │   └── image_n.webp
    ├── chapter_2/
    │   ├── image_1.webp
    │   └── image_n.webp
    └── chapter_n/
        ├── image_1.webp
        └── image_n.webp
```

## Tech Stack
- **Language**: Python 3.14.5 (standard library only for main zip extraction: `zipfile`, `os`, `re`, `shutil`, `argparse`).
- **Dependencies**: `Pillow` (v12.2.0) for converting the cover image to JPEG (`cover.jpg`).

## Commands
- **Run Parser**:
  `python parser.py --source ./source --output ./output`
- **Run Tests**:
  `python -m unittest discover -s tests`

## Project Structure
```
d:\Download\book-parse\
├── source/                  # Input CBR files (provided)
├── output/                  # Output directory (generated)
├── parser.py                # Main parsing CLI script
├── tests/                   # Automated unit tests
│   └── test_parser.py       # Unit tests for parsing logic
├── spec.md                  # Project specification (this file)
└── implementation_plan.md   # Detailed implementation plan
```

## Code Style
- **Python PEP 8** standard.
- Typed function signatures.
- Clean logging of progress (e.g. printing volume progress, chapter creation, and page count).
- Example snippet:
```python
def extract_chapter_id(filename: str) -> str:
    """Extracts chapter identifier (e.g. 'c001', 'c005x1') from a page filename."""
    match = re.search(r' - (c\d+(?:x\d+)?) ', filename)
    if match:
        return match.group(1)
    return ""
```

## Testing Strategy
- **Framework**: `unittest` (Python built-in).
- **Unit Tests**:
  - Test regex matching for Series Title extraction.
  - Test regex matching for Chapter ID and Page ID extraction.
  - Mock zipfile reading and file system writing to test grouping and ordering logic.
  - Verify cover image selection logic.

## Boundaries
- **Always**:
  - Keep the original `.webp` page images intact, extracting them without transcoding (only transcode/convert the `cover.jpg` file).
  - Sort pages numerically by page number (e.g., `p001` before `p002-p003` before `p004`).
  - Sort chapters naturally (e.g. `c001`, `c002`, ..., `c005`, `c005x1`, `c005x2`, `c006`).
- **Ask First**:
  - Installing any third-party library other than `Pillow`.
- **Never**:
  - Modify the input files in the `source/` folder.
  - Delete or overwrite files in the output folder without warnings.

## Success Criteria
1. The parser processes all `.cbr` files in the source directory.
2. The series title is correctly detected (e.g., `Betrayed by the Hero, I Formed a MILF Party With His Mom!`).
3. A single `cover.jpg` is generated at the root of the series directory (extracted from the first volume's cover webp page and converted to JPEG).
4. Chapter folders are correctly generated using the format `chapter_[number]` or `chapter_[number]_extra_[suffix]` (e.g., `chapter_1`, `chapter_5_extra_1`).
5. Pages are saved inside each chapter folder as `image_1.webp`, `image_2.webp`, etc., in correct reading order.
6. The test suite passes with 100% success rate.
