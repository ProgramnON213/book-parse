# Implementation Plan: Code Simplification, Hardening, and Optimization

## Overview
Address issues identified in the code quality review to improve safety, Windows compatibility, memory efficiency, and readability.

## Architecture Decisions
- Resolve symbolic links using `os.path.realpath` in path safety verification.
- Wrap Windows path comparisons in `try-except ValueError` blocks to support multi-drive path boundaries.
- Extract individual book extraction into a helper function `process_single_book` to keep code modular and simplify control flow.
- Stream zip members using `shutil.copyfileobj` to prevent memory spikes on large images.
- Handle transparent cover images safely by pasting them on a white background.

## Task List

### Phase 1: Implementation
- [ ] Task 1: Refactor `check_safe_path` to resolve symlinks and catch ValueError on Windows drive mismatches.
- [ ] Task 2: Extract `process_single_book` helper function, grouping zip bomb limits checks and page filtering into a single loop, and creating directory only when valid pages exist.
- [ ] Task 3: Stream file extraction using `shutil.copyfileobj`.
- [ ] Task 4: Add transparency handling for cover image conversion to JPEG.
- [ ] Task 5: Verify all unit tests pass, and add new test cases if necessary.

### Checkpoint: Verification
- [ ] Automated tests pass successfully.
