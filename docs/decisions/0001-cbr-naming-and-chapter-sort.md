# ADR-0001: CBR Filename Output Mapping and Natural Sorting

## Status
Accepted

## Date
2026-07-17

## Context
We need to parse `.cbr` comic archives, group their page images by chapter, and output them to a local folder tree. The main requirements are:
1. Identifying which individual books (CBR archives) have already been successfully processed.
2. Sorting chapters naturally (including special chapters like `c005x1` or `c005x2`).
3. Retaining image format for pages while converting the cover image to JPEG `cover.jpg` for media server compatibility.

## Decision
1. **Filename-Based Directories**: Each `.cbr` file is processed independently. Its output folder is named exactly after the CBR filename (minus the `.cbr` extension).
2. **Tuple-Based Natural Sorting**: Chapter strings are mapped to sorting keys representing `(chapter_number, extra_number)`. E.g., `c005` maps to `(5, 0)` and `c005x1` maps to `(5, 1)`. These are then formatted into folder names: `chapter_5` and `chapter_5_extra_1`.
3. **Pillow JPEG Conversion**: The cover page (matching `[Cover]` or `p000`) is extracted from each zip, converted to RGB, and saved as a `.jpg` image, while other pages remain in their original webp format.

## Alternatives Considered

### Alternative A: Single Series Directory Grouping
- Group all pages from all CBR files under a single folder based on series title (e.g. `local/Betrayed by the Hero.../`).
- *Pros*: Keeps the whole series unified.
- *Cons*: Difficult to trace which volumes/archives were successfully processed.
- *Status*: **Rejected** in favor of explicit CBR naming to solve the status tracking problem.

### Alternative B: External state tracking database/JSON
- Keeping a state JSON mapping file names to extraction timestamps.
- *Pros*: Allows grouping in a single folder while knowing what's done.
- *Cons*: Adds file writing overhead, state corruption risks, and makes it harder for the user to verify status visually.
- *Status*: **Rejected** in favor of filename-based directories which are self-documenting.

## Consequences
- Folder structure is self-documenting: looking at `output/local/` shows exactly which books are extracted.
- Easy volume/book management.
- Zero-config processing.
