# ADR-0004: Table of Contents (toc.json) Support and Fallback Strategy

## Status
Accepted

## Date
2026-07-25

## Context
When processing comic archives (`.cbr`, `.cbz`, `.zip`), chapter identification previously relied entirely on regex matching in page filenames (such as `c001` or `c005x1`). However, many archives lack explicit chapter tags in page filenames or use non-standard page naming. Additionally, the `toc-extractor` tool generates structured `toc.json` files containing exact chapter metadata and 1-indexed page boundaries (`start_page` and `end_page`).

We needed to:
1. Support reading `toc.json` both embedded inside archives and provided externally alongside archive files in the source directory.
2. Use `toc.json` chapter page boundaries to slice pages into chapter folders when available.
3. Preserve `toc.json` metadata in the output book directory (`output/local/[BookName]/toc.json`) for downstream reader apps.
4. Maintain a robust fallback to existing regex-based parsing when `toc.json` is missing or invalid.

## Decision
1. **`toc.json` Resolution Hierarchy**:
   - Check inside the archive for `toc.json` (case-insensitive search).
   - If not found in the archive, check the `--source` directory for `[book_stem].toc.json` or `toc.json`.
2. **Page-Range Slicing & Outlier Routing**:
   - Sort all valid image pages naturally into a 1-indexed ordered list.
   - Assign images within `[start_page, end_page]` ranges to their corresponding chapter IDs (e.g. `c001` -> `chapter_1`).
   - Chapter entries in `toc.json` without explicit `cXXXX` IDs (e.g. `finale`, `appendix`, `afterword`) are assigned sequential chapter IDs (`c007` -> `chapter_7`, `c008` -> `chapter_8`), continuing monotonically from the highest numeric chapter ID.
   - Leading pages before Chapter 1 (`i < first_chapter.start_page`) are assigned to `c000` (`chapter_0`).
   - Intermediate gap pages between chapters and trailing pages past the last chapter are strictly isolated into extra chapters (`c{N}x1` -> `chapter_N_extra_1`).
3. **Output Metadata Preservation**:
   - Copy/write `toc.json` to `output/local/[BookName]/toc.json` whenever present.
4. **Graceful Fallback**:
   - If `toc.json` is missing, unparseable, or malformed, fall back 100% to regex filename chapter matching.

## Alternatives Considered

### Alternative A: Requiring `toc.json` for all books
- *Pros*: Guarantees consistent metadata for every extracted book.
- *Cons*: Breaks compatibility with archives that do not contain a Table of Contents.
- *Status*: **Rejected** in favor of automatic fallback to regex chapter matching.

### Alternative B: Overriding chapter folder names with custom chapter titles from `toc.json`
- *Pros*: Folder names include descriptive titles (e.g. `chapter_1_the_beginning`).
- *Cons*: Breaks filesystem path predictability and existing regex-based folder conventions (`chapter_[number]`).
- *Status*: **Rejected** in favor of keeping standardized `chapter_[number]` folder paths while preserving full metadata in `toc.json`.

## Consequences
- Books with AI-extracted or custom `toc.json` files are automatically parsed with exact chapter boundaries.
- Full chapter metadata is accessible at `output/local/[BookName]/toc.json`.
- Archives without `toc.json` continue to work seamlessly without breaking changes.
