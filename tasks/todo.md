# Todo Checklist: ZIP File Support

- [x] Update `parser.py` scanner to include `.zip` files
- [x] Add digit extraction fallback in `extract_page_info`
- [x] Update default chapter ID to `c001`
- [x] Update cover selection fallback to pick first naturally sorted page
- [x] Add unit test `test_process_books_zip_plain_filenames` in `tests/test_parser.py`
- [x] Run `python -m unittest discover -s tests` to verify all tests pass
