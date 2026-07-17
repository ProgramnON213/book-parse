# Spec: CBR Book Parser

## Objective
The program will parse a set of `.cbr` (renamed `.zip` archives containing webp images) files in a source directory, group pages by chapter, and organize them into an output structure where each `.cbr` file gets its own directory named after the CBR filename (excluding the `.cbr` extension).

Specifically, it will take files from:
`source/[filename].cbr`

And output the following structure to a target storage directory:
```
[storage_location]/local/
└── [CBR filename without extension]/
    ├── cover.jpg
    ├── chapter_1/
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
- Clean logging of progress (e.g. printing book processing progress, chapter creation, and page count).

## Testing Strategy
- **Framework**: `unittest` (Python built-in).
- **Unit Tests**:
  - Test regex matching for Chapter ID and Page ID extraction.
  - Test regex matching for extracting the output folder name from the CBR file.
  - Mock zipfile reading and file system writing to test grouping and ordering logic.
  - Verify cover image selection logic.

## Boundaries
- **Always**:
  - Keep the original `.webp` page images intact, extracting them without transcoding (only transcode/convert the `cover.jpg` file).
  - Sort pages numerically by page number.
  - Sort chapters naturally (e.g. `c001`, `c002`, ..., `c005`, `c005x1`, `c005x2`, `c006`).
- **Ask First**:
  - Installing any third-party library other than `Pillow`.
- **Never**:
  - Modify the input files in the `source/` folder.
  - Delete or overwrite files in the output folder without warnings.

## Success Criteria
1. The parser processes all `.cbr` files in the source directory.
2. For each `.cbr` file processed, a corresponding folder named after the filename (no extension) is created in `output/local/`.
3. A single `cover.jpg` is generated at the root of each book directory (extracted from that book's cover webp page and converted to JPEG).
4. Chapter folders are correctly generated inside each book directory using the format `chapter_[number]` or `chapter_[number]_extra_[suffix]` (e.g., `chapter_1`, `chapter_5_extra_1`).
5. Pages are saved inside each chapter folder as `image_1.webp`, `image_2.webp`, etc., in correct reading order.
6. The test suite passes with 100% success rate.
