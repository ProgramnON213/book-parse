# CBR/CBZ/ZIP Book Parser

A Python command-line utility to extract, sort, and organize image pages from Comic Book archives (`.cbr`, `.cbz`, and `.zip` files) into a structured chapter hierarchy with a JPEG cover.

## Objective
For each `.cbr`, `.cbz`, or `.zip` book in the `source/` folder, the utility parses the archive, identifies chapter/page sequences, filters out non-image files, and extracts them into a dedicated folder matching the book filename. This establishes a 1-to-1 mapping so you can immediately see which books have been successfully extracted.

## Output Structure
```
output/local/
└── [Book filename without extension]/
    ├── cover.jpg
    ├── chapter_1/
    │   ├── image_1.png
    │   └── image_n.webp
    └── chapter_n/
        ├── image_1.webp
        └── image_n.jpg
```

## Quick Start

1. **Clone or copy this repository** into your workspace.
2. **Install dependencies**:
   ```bash
   pip install Pillow
   ```
3. **Place your books**: Put your `.cbr`, `.cbz`, or `.zip` archives inside the `source/` folder.
4. **Run the parser**:
   ```bash
   python parser.py --source ./source --output ./output
   ```

## Development Commands

| Command | Description |
|---------|-------------|
| `python parser.py --source <dir> --output <dir>` | Runs the parser |
| `python -m unittest discover -s tests` | Runs the full automated test suite |

## Naming Conventions & Logic
- **Output Folder**: Named exactly after the book file (excluding the extension).
- **Cover Image**: Extracted from the page flagged `[Cover]` or `p000` inside the archive, converted to RGB JPEG (safe transparency handling included), and saved as `cover.jpg`. If no cover marker exists, the first naturally sorted image page is automatically selected as `cover.jpg`.
- **Chapter Folders**:
  - Standard chapters (e.g., `c001`) -> `chapter_1`
  - Extra chapters (e.g., `c005x1`) -> `chapter_5_extra_1`
  - Files without explicit chapter tags default to `chapter_1`.
- **Pages**: Named sequentially as `image_1.[ext]`, `image_2.[ext]`, etc., keeping their original file extensions (e.g. `.webp`, `.png`, `.jpg`, `.jpeg`), and ordered numerically by page number or numerical filename (e.g. `1.jpg`, `2.jpg`, `10.jpg`). Non-image files (`.txt`, `.nfo`, `.DS_Store`) are automatically ignored.

