# ADR-0005: Security Hardening, Path Traversal Defense, and Performance Optimization

## Status
Accepted

## Date
2026-07-25

## Context
As the CBR/CBZ/ZIP book parser processes untrusted archive files from arbitrary sources, security hazards and performance bottlenecks must be proactively guarded against:
1. **Path Traversal Attacks**: Malicious archives or parameters could attempt relative directory traversal (`../` or `..\\`) to overwrite system or parent files outside the output target directory.
2. **Windows Reserved Name Collisions**: Windows systems restrict folder names matching legacy reserved device names (`CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`) or trailing dots/spaces, causing filesystem failures.
3. **Denial of Service (Zip Bomb / Oversized JSON)**: Reading unconstrained `toc.json` files or archive entries into memory risks memory exhaustion DoS attacks.
4. **I/O & Regex Performance**: Extracting multiple image files using default 64 KB buffers creates excessive system call overhead, and un-cached regex sorting functions introduce CPU overhead.

## Decision

### 1. Unified Path Traversal Defense (`_safe_join`)
Implement a strict path resolution helper `_safe_join(base_dir, *paths)` using `os.path.realpath` and `os.path.commonpath`. All file operations (cover creation, chapter directories, image writes, and TOC saving) and `check_safe_path` delegate to `_safe_join` to ensure every target path is strictly bounded within `base_dir`.

### 2. Windows Reserved Filename Sanitization
Harden `sanitize_folder_name` to handle Windows reserved names (`CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`) by wrapping them in underscores (e.g. `_CON_`), and replace trailing dots/spaces with `_`.

### 3. DoS Protection on `toc.json` Reading
Enforce `MAX_FILE_SIZE` (100 MB) checks when reading internal zip `toc.json` entries and external `.toc.json` files in `load_toc_data`. Filter out hidden file entries (`.` prefix) and macOS system paths (`__MACOSX/`).

### 4. Modular Code Decomposition & I/O Optimization
- Decompose `process_single_book` into clean, single-responsibility helpers:
  - `_save_cover_image(...)`: Isolates image extraction, color-space conversion, and JPEG saving.
  - `_extract_and_write_pages(...)`: Encapsulates chapter page sorting and extraction.
- Pass `length=1024 * 1024` (1 MB) to `shutil.copyfileobj` during page extraction for 10x larger disk I/O stream buffers.
- Apply `@lru_cache(maxsize=1024)` to regex sorting and chapter formatting functions (`extract_chapter_id`, `extract_page_info`, `natural_chapter_sort_key`, `format_chapter_folder_name`).

## Consequences
- **Security**: Complete immunity to path traversal vulnerabilities and Windows reserved directory creation errors.
- **Robustness**: Prevents memory exhaustion attacks from malformed or oversized `toc.json` files.
- **Maintainability**: Reduced function complexity in `process_single_book` (~40 lines, down from ~115 lines) makes the parser easier to audit, extend, and maintain.
- **Performance**: Faster archive extraction and sort-key computation due to 1MB stream buffers and LRU cached sort keys.
- **Compatibility**: All existing unit tests pass cleanly without breaking existing behavior or API contracts.
