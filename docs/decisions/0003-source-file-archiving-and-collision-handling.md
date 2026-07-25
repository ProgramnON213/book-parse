# ADR-0003: Automatic Source File Archiving, Timestamp Collision Resolution, and Execution Summary

## Status
Accepted

## Date
2026-07-25

## Context
When processing comic book archives (`.cbr`, `.cbz`, `.zip`), extracted books were placed into the output folder, but the original source files remained in the `--source` directory. On subsequent parser runs, these source files were repeatedly re-scanned and re-extracted, wasting CPU and disk I/O.

To address this, we needed:
1. Automatic moving of parsed source files out of `--source` into an archive directory.
2. Collision resolution when an archive file with the same name already exists in the target archive directory.
3. Retention of failed or corrupted archives in `--source` for user inspection.
4. Clear execution feedback summarizing metrics across the run.

## Decision
1. **Default Archiving Behavior**: Enable automatic file archiving by default, moving successfully parsed source files to `--archive` (default `./archive`). Archiving can be configured or disabled via the `--archive` CLI flag.
2. **Timestamp Collision Resolution**: If a file with the same name already exists in `--archive`, append a timestamp suffix (`_YYYYMMDD_HHMMSS`) to the filename stem before moving (e.g. `book_20260725_081443.cbz`).
3. **Failure Isolation**: If archive parsing fails due to zip corruption, size limit violations, or bad paths, leave the source file in `--source` so the user is aware it requires attention.
4. **Path Boundary Validation**: Validate `--archive` paths with `check_safe_path` to prevent path traversal vulnerability vectors.
5. **Execution Summary Reporting**: Output a formatted summary block at the end of parser execution detailing:
   - Total books found
   - Successfully parsed count
   - Archived count
   - Failed / skipped count

## Alternatives Considered

### Alternative A: Deleting source files upon completion
- *Pros*: Simple implementation.
- *Cons*: High risk of irreversible data loss if extraction succeeded partially or if user wanted to retain original archives.
- *Status*: **Rejected** in favor of moving files to a dedicated archive directory.

### Alternative B: Overwriting existing files in archive directory
- *Pros*: Keeps archive filenames clean and static.
- *Cons*: Risks overwriting an earlier version of an archive with the same filename.
- *Status*: **Rejected** in favor of non-destructive timestamp suffixes.

## Consequences
- Subsequent parser runs in `--source` only process new books, eliminating redundant parsing work.
- Existing archive files are never overwritten unintentionally.
- Corrupted files are visibly retained in `--source` for easy identification.
- Users receive clear diagnostic summary metrics in their terminal after every execution run.
