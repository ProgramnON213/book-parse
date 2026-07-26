# ADR-0007: Uncompressed Directory Book Support

## Status
Accepted

## Date
2026-07-26

## Context
Comic and manga books frequently exist on disk as uncompressed folders of images (loose page files or nested subfolders) rather than compressed `.cbz` or `.cbr` archive files. Requiring users to manually compress these folders into ZIP/RAR archives before parsing creates friction.

Extending `book-parse` to handle uncompressed book directories in `--source` required addressing the following design considerations:
1. **Zero-Code-Duplication Abstraction**: The core parser logic (`load_toc_data`, `_save_cover_image`, `_extract_and_write_pages`, `process_single_book`) should treat uncompressed directories identically to file archives without duplicating file discovery, sorting, cover generation, or chapter grouping routines.
2. **Strict Filtering**: Only supported image files (`.webp`, `.jpg`, `.jpeg`, `.png`) and `toc.json` should be processed. Hidden directories (`.`), system folders (`__MACOSX`), and non-image files should be safely ignored.
3. **Source Archiving Parity**: Parsed source directories in `--source` should be moved to `--archive` upon successful completion, using existing timestamp suffix collision handling (`_YYYYMMDD_HHMMSS`).

## Decision

### 1. Extended `ArchiveReader` Directory Mode
- Added directory handling (`archive_type = 'dir'`) to the unified `ArchiveReader` context manager.
- `ArchiveReader.is_archive(path)` now checks `os.path.isdir(path)` alongside zip/rar detection.
- `infolist()` uses `os.walk` to recursively scan directory contents, generating forward-slash relative path `ArchiveEntry` instances.
- `read(name)` and `open(name)` use `_safe_join` to securely stream or read file bytes directly from local filesystem paths.

### 2. Item Discovery in `process_books()`
- Updated `process_books()` to discover both file archives (`.zip`, `.cbz`, `.cbr`, `.rar`) and uncompressed book directories inside `--source` (skipping dot-prefixed hidden directories and `__MACOSX`).

### 3. Archive Folder Moving
- Leveraged `shutil.move()` in `archive_source_file()` which naturally supports moving both files and directories to `--archive`.

## Consequences
- **User Experience**: Users can place loose image folders directly in `--source` without needing to compress them into archives first.
- **Maintainability**: Reusing `ArchiveReader` allows all chapter grouping, cover creation, and TOC parsing logic to remain completely format-agnostic.
- **Testability**: Unit tests (`test_archive_reader_directory` and `test_process_books_directory`) confirm complete feature parity across all 34 automated unit tests.
