# Spec: CBR/CBZ/ZIP Book Parser

## Objective
The program will parse a set of `.cbr`, `.cbz`, or `.zip` (ZIP archives containing comic pages in formats like WebP, JPG, JPEG, and PNG) files in a source directory, group pages by chapter, filter out non-image files, and organize them into an output structure where each archive file gets its own directory named after the book filename (excluding the extension).

Specifically, it will take files from:
`source/[filename].cbr`, `source/[filename].cbz`, or `source/[filename].zip`

And output the following structure to a target storage directory:
```
[storage_location]/local/
└── [Book filename without extension]/
    ├── cover.jpg
    ├── chapter_1/
    │   ├── image_1.png
    │   └── image_n.webp
    └── chapter_n/
        ├── image_1.webp
        └── image_n.jpg
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
├── source/                  # Input CBR/CBZ/ZIP files (provided)
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
  - Test regex matching for extracting the output folder name from the CBR/CBZ/ZIP file.
  - Test plain numerical page filename sorting (`1.jpg`, `2.jpg`, `10.jpg`) and default `chapter_1` placement.
  - Mock zipfile reading and file system writing to test grouping and ordering logic.
  - Verify cover image selection logic and automatic fallback to first image.

## Boundaries
- **Always**:
  - Keep the original page images intact (supporting .webp, .jpg, .jpeg, .png), extracting them without transcoding (only transcode/convert the cover.jpg file).
  - Filter out non-image files (`.txt`, `.nfo`) and hidden system files (`.DS_Store`, `__MACOSX`).
  - Sort pages numerically by page number or filename stem digits.
  - Sort chapters naturally (e.g. `c001`, `c002`, ..., `c005`, `c005x1`, `c005x2`, `c006`).
- **Ask First**:
  - Installing any third-party library other than `Pillow`.
- **Never**:
  - Modify the input files in the `source/` folder.
  - Delete or overwrite files in the output folder without warnings.

## Success Criteria
1. The parser processes all `.cbr`, `.cbz`, and `.zip` files in the source directory.
2. For each file processed, a corresponding folder named after the filename (no extension) is created in `output/local/`.
3. A single `cover.jpg` is generated at the root of each book directory (extracted from `[Cover]`/`p000` or automatically picked from the first naturally sorted image page).
4. Chapter folders are correctly generated inside each book directory using the format `chapter_[number]` or `chapter_[number]_extra_[suffix]` (e.g., `chapter_1`, `chapter_5_extra_1`), defaulting to `chapter_1` for un-tagged archives.
5. Pages are saved inside each chapter folder as `image_1.webp`, `image_2.webp`, etc., in correct reading order.
6. The test suite passes with 100% success rate.

