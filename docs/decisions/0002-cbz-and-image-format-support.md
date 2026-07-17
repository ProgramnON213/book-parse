# ADR-0002: CBZ Support, Path Safety, and Performance Optimization

## Status
Accepted

## Date
2026-07-18

## Context
We need to expand the comic book parser to support `.cbz` archives alongside `.cbr` archives. Additionally, we need to handle different image formats (.webp, .jpg, .jpeg, .png) inside these archives, ensure path safety (preventing directory traversals and resolving symbolic links), and optimize resource usage when extracting files (preventing memory spikes on large archive members).

## Decision
1. **Case-Insensitive File Matching**: Search the source directory for both `.cbr` and `.cbz` extensions case-insensitively using `.lower().endswith(('.cbr', '.cbz'))`.
2. **Multi-Format Extraction**: Scan zip archives for `.webp`, `.jpg`, `.jpeg`, and `.png` image formats, maintaining their original extensions when renaming to `image_{i}.[ext]`.
3. **Symbolic Link Resolution in Path Checks**: Update `check_safe_path` to use `os.path.realpath` instead of `os.path.abspath` to correctly resolve symlinks before checking boundaries.
4. **Windows Drive Mismatch Protection**: Catch `ValueError` in path comparison inside `check_safe_path` to avoid crashes on Windows systems when base and target directories lie on different drives.
5. **Streaming Extraction**: Stream zip members to disk using `shutil.copyfileobj` rather than loading the entire file into memory using `z.read()`.
6. **Robust Cover Conversion**: Render transparent covers correctly to JPEG by pasting RGBA/LA cover images onto a solid white RGB background before saving.

## Alternatives Considered

### Alternative A: Pre-converting all extracted pages to WebP
- *Pros*: Output format is strictly unified.
- *Cons*: High processing overhead, potential quality loss, and requires transcode dependencies.
- *Status*: **Rejected** in favor of preserving original formats and extensions.

### Alternative B: Extracting files directly without path checks
- *Pros*: Slightly simpler code.
- *Cons*: High security risk of directory traversal attacks (Zip Slip).
- *Status*: **Rejected** as path safety is a hard boundary constraint.

## Consequences
- The parser handles both `.cbr` and `.cbz` books cleanly.
- Extracted images are organized efficiently and keep their original fidelity and file extension.
- The utility is safer against path traversal attacks and more compatible with Windows path structures.
- Streamed file I/O prevents memory exhaustion under high-load files.
