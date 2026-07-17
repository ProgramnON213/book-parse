# Implementation Plan: Parser Code Simplification

## Overview
Simplify parts of `parser.py` by applying code-shrinking patterns identified in the ponytail audit. Specifically, we will simplify cover page selection and chapter page grouping.

## Architecture Decisions
- Keep `parser.py` external dependencies clean (only Pillow). Use stdlib `collections.defaultdict`.

## Task List

### Phase 1: Implementation
- [ ] Task 1: Simplify cover page selection in `parser.py` using `next()`
- [ ] Task 2: Simplify chapter grouping in `parser.py` using `defaultdict`

### Checkpoint: Verification
- [ ] Automated tests pass successfully.
