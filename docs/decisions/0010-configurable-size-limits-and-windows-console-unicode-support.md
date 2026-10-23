# ADR-0010: Configurable Archive and File Size Limits, and Windows Console Unicode Support

## Status
Accepted

## Date
2026-10-24

## Context
As the CBR/CBZ/ZIP/RAR book parser encountered real-world high-resolution artbooks and multi-chapter manga releases, two operational issues emerged:

1. **Uncompressed Size Ceilings on Modern Media**:
   - The original security bounds set in ADR-0005 hardcoded `MAX_BOOK_UNCOMPRESSED_SIZE = 1024 * 1024 * 1024` (1 GB) and `MAX_FILE_SIZE = 100 * 1024 * 1024` (100 MB).
   - High-resolution digital artbooks and multi-chapter scan releases easily exceed 1 GB uncompressed (e.g., `'大黑塔 水着'` at ~1.49 GB across 32 ultra-high-resolution pages).
   - The parser lacked CLI flags or parameter overrides, aborting parsing on legitimate archives with an unrecoverable `ValueError`.

2. **Windows Console Unicode Encoding Exceptions**:
   - On Windows environments, Python standard streams (`sys.stdout`, `sys.stderr`) default to legacy single-byte encodings (e.g. `cp1252` or OEM codepages) unless explicit environment flags are set.
   - When printing progress or error messages containing CJK ideographs or non-ASCII book titles, execution crashed with `UnicodeEncodeError`.

## Decision

1. **Raised Default Security Bounds**:
   - Raised default `MAX_BOOK_UNCOMPRESSED_SIZE` from 1 GB to **4 GB** (`4 * 1024 * 1024 * 1024` bytes).
   - Raised default `MAX_FILE_SIZE` from 100 MB to **200 MB** (`200 * 1024 * 1024` bytes).

2. **Human-Readable Size String Parser (`parse_size`)**:
   - Implemented a robust size string parser supporting units: `B`, `KB`/`KiB`, `MB`/`MiB`, `GB`/`GiB`, and `TB`/`TiB` (case-insensitive, e.g. `"4GB"`, `"500MB"`, `"1.5gb"`), integer byte counts, and `"0"` for unlimited / disabled size checks.

3. **Configurable CLI & API Parameters**:
   - Added `--max-book-size` and `--max-file-size` CLI arguments to `parser.py`.
   - Plumbed `max_book_size` and `max_file_size` through `process_books` and `process_single_book`.
   - Forwarded `eff_max_file_size` into `load_toc_data`, `load_meta_data`, and `_find_and_load_json`.
   - Treated `0` or non-positive values as unlimited, completely bypassing size checks when requested.

4. **Windows Console Unicode Reconfiguration**:
   - Added automatic UTF-8 stream reconfiguration for `sys.stdout` and `sys.stderr` with `errors='replace'` at module startup.

5. **Test-Driven Verification**:
   - Added unit tests in `tests/test_parser.py` validating `parse_size` parsing and errors, book-level size enforcement, custom size ceilings, unlimited overrides (`0`), and CLI argument parsing.

## Alternatives Considered

### Alternative A: Completely Remove Size Limits
- *Pros*: Never triggers size-limit errors.
- *Cons*: Leaves the parser completely vulnerable to Denial of Service (DoS) and zip-bomb attacks (e.g., small zip files expanding into hundreds of gigabytes).
- *Status*: **Rejected**. Retaining safe default limits with configurable CLI flags provides both security and flexibility.

### Alternative B: Raise Hardcoded Constant Without CLI Options
- *Pros*: Simplest code change.
- *Cons*: Still fails on 8 GB+ omnibus collections, and prevents security-conscious users from tightening limits in resource-constrained environments.
- *Status*: **Rejected** in favor of `--max-book-size` and `--max-file-size`.

## Consequences
- Legitimate high-resolution digital books and art collections parse cleanly out of the box without requiring manual flag tuning.
- Users have full control over size limits for edge cases (e.g. `--max-book-size 8GB` or `--max-book-size 0`).
- No crashes on non-ASCII book titles on Windows terminals.
- 100% test pass rate across 40 unit and integration tests.
