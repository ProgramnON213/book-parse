# ADR-0009: Code Quality Refactoring, DRY JSON Loading, and Direct Attribute Model

## Status
Accepted

## Date
2026-07-26

## Context
As the `book-parse` utility expanded to support multiple archive formats (CBZ, CBR, ZIP, RAR), uncompressed directories, Table of Contents (`toc.json`), and metadata extraction (`meta.json`), certain code structures accumulated indirection and logic duplication:
1. `load_toc_data` and `load_meta_data` contained ~100 lines of duplicate scanning, size verification, reading, UTF-8 BOM decoding, and parsing logic.
2. `ArchiveEntry` used a private `_is_dir` field with an `.is_dir()` method getter, creating unnecessary indirection for a read-only dataclass.
3. `check_safe_path` acted as a pass-through wrapper around `_safe_join` with exception-swallowing behavior.
4. Low-frequency functions (`format_chapter_folder_name`) held speculative `@lru_cache` decorators despite being invoked only once per chapter.

## Decision
1. **Unified JSON Data Loader (`_find_and_load_json`)**:
   - Extract a generic helper function `_find_and_load_json(target_name, archive_path, z, validator_fn)` that encapsulates internal archive scanning, system/hidden path filtering (`.`, `__MACOSX`), `MAX_FILE_SIZE` safety checks, UTF-8 BOM decoding, and sidecar file resolution in `--source`.
   - Refactor `load_toc_data` and `load_meta_data` to delegate directly to `_find_and_load_json`.
2. **Direct Dataclass Attributes (`ArchiveEntry`)**:
   - Simplify `ArchiveEntry` dataclass to expose `is_dir: bool` directly as a public field (`ArchiveEntry(filename, file_size, is_dir)`), removing `_is_dir` and the `.is_dir()` method.
3. **Direct Path Validation (`_safe_join`)**:
   - Remove the `check_safe_path` pass-through wrapper.
   - Update `archive_source_file` to invoke `_safe_join(base_dir, archive_dir)` directly when `base_dir` is provided, retaining explicit exception context.
4. **YAGNI Speculative Cache Removal**:
   - Remove `@lru_cache` on `format_chapter_folder_name`. Retain `@lru_cache` only on high-frequency regex parsing functions (`extract_chapter_id`, `extract_page_info`, `natural_chapter_sort_key`).
5. **Metadata Default Value Hygiene**:
   - Update `transform_meta_to_details` to use `str(meta_data.get("artist") or "")` and `str(meta_data.get("author") or "")` to ensure `None` values produce empty string defaults instead of `"None"` literal strings.

## Alternatives Considered

### Alternative A: Keep Separate `load_toc_data` and `load_meta_data` implementations
- *Pros*: Functions remain isolated without a shared helper parameter.
- *Cons*: Duplicate code across two complex JSON scanning loops increases maintenance overhead and risk of inconsistent security check drift.
- *Status*: **Rejected** in favor of `_find_and_load_json`.

### Alternative B: Retain `is_dir()` Method on `ArchiveEntry`
- *Pros*: Preserves method call syntax `entry.is_dir()`.
- *Cons*: Adds unnecessary indirection for a simple Python `@dataclass`.
- *Status*: **Rejected** in favor of direct `is_dir` field access.

## Consequences
- Codebase size reduced by ~100 lines while improving readability and maintainability.
- Eliminated wrapper indirection and redundant exception swallowing.
- Maintained 100% test pass rate with full test suite coverage.
