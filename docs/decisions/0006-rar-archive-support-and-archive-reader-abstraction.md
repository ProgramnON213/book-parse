# ADR-0006: RAR Archive Support and Unified ArchiveReader Abstraction

## Status
Accepted

## Date
2026-07-26

## Context
Manga and comic book digital releases frequently distribute books in RAR format (`.rar` extension) or RAR-compressed CBR format (`.cbr` extension). Previously, `book-parse` relied exclusively on Python's built-in `zipfile.ZipFile` module, which meant actual RAR-compressed archives could not be processed and were skipped with warning errors.

Adding RAR archive support introduced several technical challenges:
1. **API Parity across Archive Drivers**: `zipfile.ZipFile` and `rarfile.RarFile` have minor API differences (e.g. `zip_info.is_dir()` vs `rar_info.isdir()`, or `rarfile` requiring third-party library installation).
2. **Backward Compatibility & Optional Dependencies**: Environments without `rarfile` or `unrar` binaries installed must continue processing standard ZIP/CBZ archives seamlessly without crashing or raising unhandled `ImportError` exceptions.
3. **Boilerplate Minimization**: Abstracting entries and archive reader objects should avoid bloated manual classes or redundant loop branching.

## Decision

### 1. Unified `ArchiveReader` Context Manager and `@dataclass ArchiveEntry`
- Created a lightweight context-manager wrapper `ArchiveReader` in `parser.py` that encapsulates both `zipfile.ZipFile` and `rarfile.RarFile`.
- Created `@dataclass class ArchiveEntry` (`filename`, `file_size`, `_is_dir`) to provide a uniform entry schema across zip and rar drivers.
- Implemented `ArchiveReader.infolist()` using a clean, single-pass list comprehension that resolves driver-specific directory checks (`is_dir()` vs `isdir()`).

### 2. Format Auto-Detection & Soft Dependency
- Implemented `ArchiveReader.is_archive(path)` which dynamically checks `zipfile.is_zipfile(path)` and `rarfile.is_rarfile(path)`.
- Handled `rarfile` as an optional module via `try...except ImportError`. If a `.rar` file is encountered in `--source` without `rarfile` installed, `book-parse` logs a clear user warning (`"requires the 'rarfile' package. Please install it with 'pip install rarfile'"`) and gracefully skips the file while preserving normal processing for all ZIP archives.

### 3. Complete Feature Parity
- All existing processing pipelines — `toc.json` extraction, regex page sorting, cover generation (`cover.jpg`), chapter directory routing, DoS size bounds checking, path safety (`_safe_join`), and auto-archiving to `--archive` — apply identically to RAR archives.

## Consequences
- **Usability**: Users can now process `.rar` archives and true RAR-compressed `.cbr` comic books seamlessly alongside `.zip` and `.cbz` files.
- **Maintainability**: The `ArchiveReader` abstraction isolates archive I/O, allowing parser logic to remain completely agnostic of underlying archive formats.
- **Robustness & Testability**: Mocked and real unit tests verify archive extraction, error handling, and graceful dependency fallbacks across all 30 tests in the test suite.
