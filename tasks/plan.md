# Implementation Plan: Metadata Extraction (meta.json to details.json)

## Overview
Add capability to `parser.py` to extract `meta.json` (found inside book archives or alongside in `--source`) and write formatted `details.json` into the book output folder alongside `cover.jpg`. Provide a new CLI argument `--meta` (default `"n20"`). If no `meta.json` is found, parsing proceeds normally without generating `details.json`.

## Architecture Decisions
- **Discovery Strategy**: Follow `toc.json` pattern in `parser.py` — search inside archive first, then alongside archive in source directory (`[stem].meta.json` and `meta.json`).
- **Engine Extensibility**: Engine flag `meta_engine` defaults to `"n20"`. `transform_meta_to_details` handles `n20` schema mapping.
- **Safety**: Apply `MAX_FILE_SIZE` bounds checking and `_safe_join` for file path resolution.

## Task List

### Phase 1: Core Implementation
- [ ] Task 1: Add `load_meta_data` and `transform_meta_to_details` helper functions in `parser.py`.
- [ ] Task 2: Integrate `meta.json` loading and `details.json` output writing into `process_single_book`, `process_books`, and CLI argument `--meta`.

### Phase 2: Testing & Verification
- [ ] Task 3: Add unit tests in `tests/test_parser.py` covering `meta.json` discovery, transformation, `details.json` output, missing `meta.json` fallback, and CLI args.

## Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Malformed `meta.json` | Low | Catch JSON decode errors, log warning, skip `details.json` without failing book processing. |
| Missing fields in `meta.json` | Low | Use fallback logic (`title`, `author`, `artist` default to `""`, `genre` to `[]`). |
