# CBR Book Parser

A Python command-line utility to extract, sort, and organize `.webp` pages from Comic Book RAR/ZIP archives (`.cbr` files) into a structured chapter hierarchy with a JPEG cover.

## Objective
For each `.cbr` book in the `source/` folder, the utility parses the archive, identifies chapter/page sequences, and extracts them into a dedicated folder matching the book filename. This establishes a 1-to-1 mapping so you can immediately see which books have been successfully extracted.

## Output Structure
```
output/local/
└── [CBR filename without extension]/
    ├── cover.jpg
    ├── chapter_1/
    │   ├── image_1.webp
    │   └── image_n.webp
    └── chapter_n/
        ├── image_1.webp
        └── image_n.webp
```

## Quick Start

1. **Clone or copy this repository** into your workspace.
2. **Install dependencies**:
   ```bash
   pip install Pillow
   ```
3. **Place your books**: Put your `.cbr` archives inside the `source/` folder.
4. **Run the parser**:
   ```bash
   python parser.py --source ./source --output ./output
   ```

## Development Commands

| Command | Description |
|---------|-------------|
| `python parser.py --source <dir> --output <dir>` | Runs the parser |
| `python -m unittest discover -s tests` | Runs the full automated test suite |

## Naming Conventions
- **Output Folder**: Named exactly after the CBR file (excluding `.cbr` extension).
- **Cover Image**: Extracted from the page flagged `[Cover]` or `p000` inside the archive, converted to RGB JPEG, and saved as `cover.jpg`.
- **Chapter Folders**:
  - Standard chapters (e.g., `c001`) -> `chapter_1`
  - Extra chapters (e.g., `c005x1`) -> `chapter_5_extra_1`
- **Pages**: Named sequentially as `image_1.webp`, `image_2.webp`, etc., ordered by page numbers (e.g. `p001`).
