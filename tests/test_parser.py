import os
import zipfile
import unittest
from parser import (
    extract_chapter_id,
    extract_page_info,
    natural_chapter_sort_key,
    is_cover_image,
    sanitize_folder_name,
    check_safe_path,
    archive_source_file,
    load_toc_data,
    group_pages_by_toc,
)

class TestParser(unittest.TestCase):
    def test_extract_chapter_id(self):
        self.assertEqual(
            extract_chapter_id("Betrayed by the Hero, I Formed a MILF Party With His Mom! - c001 (v01) - p000 [Cover] [dig] [Seven Seas Entertainment] [kaOak].webp"),
            "c001"
        )
        self.assertEqual(
            extract_chapter_id("Betrayed by the Hero, I Formed a MILF Party With His Mom! - c005x1 (v01) - p179 [Afterword] [dig] [Seven Seas Entertainment] [kaOak].webp"),
            "c005x1"
        )
        self.assertEqual(
            extract_chapter_id("Betrayed by the Hero, I Formed a MILF Party With His Mom! - c005x2 (v01) - p180 [dig] [Seven Seas Entertainment] [kaOak].webp"),
            "c005x2"
        )

    def test_extract_page_info(self):
        # Single page: p001 -> 1
        self.assertEqual(
            extract_page_info("Betrayed by the Hero, I Formed a MILF Party With His Mom! - c001 (v01) - p001 [dig] [Seven Seas Entertainment] [kaOak].webp"),
            1
        )
        # Combined pages: p174-p175 -> 174
        self.assertEqual(
            extract_page_info("Betrayed by the Hero, I Formed a MILF Party With His Mom! - c005 (v01) - p174-p175 [dig] [Seven Seas Entertainment] [kaOak] {sf}.webp"),
            174
        )

    def test_natural_chapter_sort_key(self):
        # c001 -> (1, 0)
        self.assertEqual(natural_chapter_sort_key("c001"), (1, 0))
        # c005x1 -> (5, 1)
        self.assertEqual(natural_chapter_sort_key("c005x1"), (5, 1))
        # c010 -> (10, 0)
        self.assertEqual(natural_chapter_sort_key("c010"), (10, 0))
        
        # Test sorting sorting logic
        chapters = ["c010", "c005x2", "c005x1", "c001", "c005"]
        sorted_chapters = sorted(chapters, key=natural_chapter_sort_key)
        self.assertEqual(sorted_chapters, ["c001", "c005", "c005x1", "c005x2", "c010"])

    def test_is_cover_image(self):
        self.assertTrue(
            is_cover_image("Betrayed by the Hero, I Formed a MILF Party With His Mom! - c001 (v01) - p000 [Cover] [dig] [Seven Seas Entertainment] [kaOak].webp")
        )
        self.assertFalse(
            is_cover_image("Betrayed by the Hero, I Formed a MILF Party With His Mom! - c001 (v01) - p001 [dig] [Seven Seas Entertainment] [kaOak].webp")
        )

    def test_process_books(self):
        import tempfile
        import shutil
        from PIL import Image
        import io

        with tempfile.TemporaryDirectory() as tmp_dir:
            source_dir = os.path.join(tmp_dir, "source")
            output_dir = os.path.join(tmp_dir, "output")
            os.makedirs(source_dir)
            os.makedirs(output_dir)

            # Generate a 1x1 WebP image byte string
            img = Image.new('RGB', (1, 1), color='red')
            webp_buffer = io.BytesIO()
            img.save(webp_buffer, format='WEBP')
            webp_bytes = webp_buffer.getvalue()

            # Create dummy CBR file
            cbr_name = "Test Book v01 (2025).cbr"
            cbr_path = os.path.join(source_dir, cbr_name)
            with zipfile.ZipFile(cbr_path, 'w') as z:
                z.writestr("Test Book - c001 (v01) - p000 [Cover].webp", webp_bytes)
                z.writestr("Test Book - c001 (v01) - p001.webp", webp_bytes)
                z.writestr("Test Book - c002 (v01) - p002.webp", webp_bytes)

            from parser import process_books
            process_books(source_dir, output_dir, archive_dir=os.path.join(tmp_dir, "archive"))

            # Check that the outputs were created correctly
            series_dir = os.path.join(output_dir, "local", "Test Book v01 (2025)")
            self.assertTrue(os.path.exists(series_dir))
            
            # Check cover.jpg
            cover_path = os.path.join(series_dir, "cover.jpg")
            self.assertTrue(os.path.exists(cover_path))
            with Image.open(cover_path) as cover_img:
                self.assertEqual(cover_img.format, "JPEG")

            # Check chapter folders
            ch1_dir = os.path.join(series_dir, "chapter_1")
            ch2_dir = os.path.join(series_dir, "chapter_2")
            self.assertTrue(os.path.exists(ch1_dir))
            self.assertTrue(os.path.exists(ch2_dir))

            # Check image extraction and ordering
            self.assertTrue(os.path.exists(os.path.join(ch1_dir, "image_1.webp")))
            self.assertTrue(os.path.exists(os.path.join(ch1_dir, "image_2.webp")))
            self.assertTrue(os.path.exists(os.path.join(ch2_dir, "image_1.webp")))

    def test_sanitize_folder_name(self):
        self.assertEqual(sanitize_folder_name("My: Cool? Book*"), "My_ Cool_ Book_")
        self.assertEqual(sanitize_folder_name("clean_name-123"), "clean_name-123")

    def test_check_safe_path(self):
        base = os.path.abspath("base_dir")
        safe = os.path.join(base, "sub", "file.txt")
        unsafe = os.path.join(base, "..", "outside.txt")
        self.assertTrue(check_safe_path(base, safe))
        self.assertFalse(check_safe_path(base, unsafe))

    def test_process_books_invalid_zip(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_dir = os.path.join(tmp_dir, "source")
            output_dir = os.path.join(tmp_dir, "output")
            os.makedirs(source_dir)
            os.makedirs(output_dir)

            # Create a file that is not a zip but ends with .cbr
            cbr_path = os.path.join(source_dir, "corrupted.cbr")
            with open(cbr_path, "w") as f:
                f.write("not a zip file")

            from parser import process_books
            # Should not raise exception
            process_books(source_dir, output_dir, archive_dir=os.path.join(tmp_dir, "archive"))
            # Verify no outputs were created
            self.assertEqual(os.listdir(output_dir), [])

    def test_process_books_zip_bomb(self):
        import tempfile
        from PIL import Image
        import io
        import parser

        with tempfile.TemporaryDirectory() as tmp_dir:
            source_dir = os.path.join(tmp_dir, "source")
            output_dir = os.path.join(tmp_dir, "output")
            os.makedirs(source_dir)
            os.makedirs(output_dir)

            img = Image.new('RGB', (1, 1), color='red')
            webp_buffer = io.BytesIO()
            img.save(webp_buffer, format='WEBP')
            webp_bytes = webp_buffer.getvalue()

            # Create dummy CBR file
            cbr_name = "Test Book.cbr"
            cbr_path = os.path.join(source_dir, cbr_name)
            with zipfile.ZipFile(cbr_path, 'w') as z:
                z.writestr("Test Book - c001 (v01) - p000 [Cover].webp", webp_bytes)
                z.writestr("Test Book - c001 (v01) - p001.webp", webp_bytes)

            # Temporarily set MAX_FILE_SIZE extremely small to trigger security exception
            old_max_file_size = parser.MAX_FILE_SIZE
            parser.MAX_FILE_SIZE = 5  # bytes
            try:
                # Should print error and skip, not crash
                parser.process_books(source_dir, output_dir, archive_dir=os.path.join(tmp_dir, "archive"))
                # Verify no output directories are created under output/local
                self.assertFalse(os.path.exists(os.path.join(output_dir, "local", "Test Book")))
            finally:
                parser.MAX_FILE_SIZE = old_max_file_size

    def test_process_books_with_subdirectories_in_zip(self):
        import tempfile
        from PIL import Image
        import io

        with tempfile.TemporaryDirectory() as tmp_dir:
            source_dir = os.path.join(tmp_dir, "source")
            output_dir = os.path.join(tmp_dir, "output")
            os.makedirs(source_dir)
            os.makedirs(output_dir)

            img = Image.new('RGB', (1, 1), color='red')
            webp_buffer = io.BytesIO()
            img.save(webp_buffer, format='WEBP')
            webp_bytes = webp_buffer.getvalue()

            # Create dummy CBR file with subdirectories inside zip
            cbr_name = "Subdir Book.cbr"
            cbr_path = os.path.join(source_dir, cbr_name)
            with zipfile.ZipFile(cbr_path, 'w') as z:
                # Place files inside folders to see if basename extraction works
                z.writestr("Manga/Cover/Subdir Book - c001 (v01) - p000 [Cover].webp", webp_bytes)
                z.writestr("Manga/Chapters/c001/Subdir Book - c001 (v01) - p001.webp", webp_bytes)

            from parser import process_books
            process_books(source_dir, output_dir, archive_dir=os.path.join(tmp_dir, "archive"))

            series_dir = os.path.join(output_dir, "local", "Subdir Book")
            self.assertTrue(os.path.exists(series_dir))
            self.assertTrue(os.path.exists(os.path.join(series_dir, "cover.jpg")))
            self.assertTrue(os.path.exists(os.path.join(series_dir, "chapter_1", "image_1.webp")))

    def test_process_books_cbz_and_formats(self):
        import tempfile
        import shutil
        from PIL import Image
        import io

        with tempfile.TemporaryDirectory() as tmp_dir:
            source_dir = os.path.join(tmp_dir, "source")
            output_dir = os.path.join(tmp_dir, "output")
            os.makedirs(source_dir)
            os.makedirs(output_dir)

            # Generate 1x1 image bytes for different formats
            img = Image.new('RGB', (1, 1), color='blue')
            
            webp_buffer = io.BytesIO()
            img.save(webp_buffer, format='WEBP')
            webp_bytes = webp_buffer.getvalue()

            png_buffer = io.BytesIO()
            img.save(png_buffer, format='PNG')
            png_bytes = png_buffer.getvalue()

            jpg_buffer = io.BytesIO()
            img.save(jpg_buffer, format='JPEG')
            jpg_bytes = jpg_buffer.getvalue()

            # Create dummy CBZ file (since it's a zip file)
            cbz_name = "Cbz Book v02 (2026).cbz"
            cbz_path = os.path.join(source_dir, cbz_name)
            with zipfile.ZipFile(cbz_path, 'w') as z:
                # Cover is a PNG image
                z.writestr("Cbz Book - c001 (v01) - p000 [Cover].png", png_bytes)
                # Page 1 is a WebP image
                z.writestr("Cbz Book - c001 (v01) - p001.webp", webp_bytes)
                # Page 2 is a JPG image
                z.writestr("Cbz Book - c001 (v01) - p002.jpg", jpg_bytes)
                # Page 3 is a PNG image
                z.writestr("Cbz Book - c002 (v01) - p003.png", png_bytes)

            from parser import process_books
            process_books(source_dir, output_dir, archive_dir=os.path.join(tmp_dir, "archive"))

            # Check that the outputs were created correctly
            series_dir = os.path.join(output_dir, "local", "Cbz Book v02 (2026)")
            self.assertTrue(os.path.exists(series_dir))
            
            # Check cover.jpg (should be JPEG, converted from PNG cover)
            cover_path = os.path.join(series_dir, "cover.jpg")
            self.assertTrue(os.path.exists(cover_path))
            with Image.open(cover_path) as cover_img:
                self.assertEqual(cover_img.format, "JPEG")

            # Check chapter folders
            ch1_dir = os.path.join(series_dir, "chapter_1")
            ch2_dir = os.path.join(series_dir, "chapter_2")
            self.assertTrue(os.path.exists(ch1_dir))
            self.assertTrue(os.path.exists(ch2_dir))

            # Check page extraction, verifying the original formats are kept
            # Sorted pages in c001:
            # 1. p000 [Cover].png -> image_1.png
            # 2. p001.webp        -> image_2.webp
            # 3. p002.jpg         -> image_3.jpg
            # Sorted pages in c002:
            # 1. p003.png         -> image_1.png
            self.assertTrue(os.path.exists(os.path.join(ch1_dir, "image_1.png")))
            self.assertTrue(os.path.exists(os.path.join(ch1_dir, "image_2.webp")))
            self.assertTrue(os.path.exists(os.path.join(ch1_dir, "image_3.jpg")))
            self.assertTrue(os.path.exists(os.path.join(ch2_dir, "image_1.png")))

    def test_process_books_cover_transparency(self):
        import tempfile
        from PIL import Image
        import io

        with tempfile.TemporaryDirectory() as tmp_dir:
            source_dir = os.path.join(tmp_dir, "source")
            output_dir = os.path.join(tmp_dir, "output")
            os.makedirs(source_dir)
            os.makedirs(output_dir)

            # Generate transparent 1x1 PNG cover image (RGBA)
            img = Image.new('RGBA', (1, 1), color=(0, 0, 255, 128))
            png_buffer = io.BytesIO()
            img.save(png_buffer, format='PNG')
            png_bytes = png_buffer.getvalue()

            # Create dummy CBZ file
            cbz_name = "Transparent Book.cbz"
            cbz_path = os.path.join(source_dir, cbz_name)
            with zipfile.ZipFile(cbz_path, 'w') as z:
                z.writestr("Transparent Book - c001 - p000 [Cover].png", png_bytes)
                z.writestr("Transparent Book - c001 - p001.png", png_bytes)

            from parser import process_books
            process_books(source_dir, output_dir, archive_dir=os.path.join(tmp_dir, "archive"))

            # Check cover is generated and converted to JPEG (without transparent details crashing)
            series_dir = os.path.join(output_dir, "local", "Transparent Book")
            cover_path = os.path.join(series_dir, "cover.jpg")
            self.assertTrue(os.path.exists(cover_path))
            with Image.open(cover_path) as cover_img:
                self.assertEqual(cover_img.format, "JPEG")

    def test_check_safe_path_exception(self):
        from unittest.mock import patch
        with patch('os.path.commonpath') as mock_commonpath:
            # Force os.path.commonpath to raise ValueError
            mock_commonpath.side_effect = ValueError("Paths don't have the same drive")
            # Should handle exception and return False, not crash
            result = check_safe_path("C:\\base", "D:\\target")
            self.assertFalse(result)

    def test_process_books_zip_plain_filenames(self):
        import tempfile
        from PIL import Image
        import io

        with tempfile.TemporaryDirectory() as tmp_dir:
            source_dir = os.path.join(tmp_dir, "source")
            output_dir = os.path.join(tmp_dir, "output")
            os.makedirs(source_dir)
            os.makedirs(output_dir)

            # Generate 1x1 image bytes
            img = Image.new('RGB', (1, 1), color='green')
            jpg_buffer = io.BytesIO()
            img.save(jpg_buffer, format='JPEG')
            jpg_bytes = jpg_buffer.getvalue()

            # Create dummy .zip file with plain numerical image names and non-image files
            zip_name = "Plain Numbers Book.zip"
            zip_path = os.path.join(source_dir, zip_name)
            with zipfile.ZipFile(zip_path, 'w') as z:
                # Non-image files that should be ignored
                z.writestr("README.txt", "Some text file content")
                z.writestr(".DS_Store", "dummy macos system file")
                
                # Plain numerical image files (written out of order)
                z.writestr("10.jpg", jpg_bytes)
                z.writestr("1.jpg", jpg_bytes)
                z.writestr("2.jpg", jpg_bytes)
                z.writestr("23.jpg", jpg_bytes)

            from parser import process_books
            process_books(source_dir, output_dir, archive_dir=os.path.join(tmp_dir, "archive"))

            # Check that output directory was created
            series_dir = os.path.join(output_dir, "local", "Plain Numbers Book")
            self.assertTrue(os.path.exists(series_dir))
            
            # Cover image should be created from the first image (1.jpg)
            cover_path = os.path.join(series_dir, "cover.jpg")
            self.assertTrue(os.path.exists(cover_path))
            with Image.open(cover_path) as cover_img:
                self.assertEqual(cover_img.format, "JPEG")

            # Default chapter folder should be chapter_1
            ch1_dir = os.path.join(series_dir, "chapter_1")
            self.assertTrue(os.path.exists(ch1_dir))

            # Images in chapter_1 should be sorted naturally: 1.jpg -> image_1, 2.jpg -> image_2, 10.jpg -> image_3, 23.jpg -> image_4
            self.assertTrue(os.path.exists(os.path.join(ch1_dir, "image_1.jpg")))
            self.assertTrue(os.path.exists(os.path.join(ch1_dir, "image_2.jpg")))
            self.assertTrue(os.path.exists(os.path.join(ch1_dir, "image_3.jpg")))
            self.assertTrue(os.path.exists(os.path.join(ch1_dir, "image_4.jpg")))
            # Verify exactly 4 image files extracted in chapter_1
            ch1_files = [f for f in os.listdir(ch1_dir) if f.startswith("image_")]
            self.assertEqual(len(ch1_files), 4)

    def test_archive_source_file_success(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_file = os.path.join(tmp_dir, "book.cbz")
            with open(source_file, "w") as f:
                f.write("dummy content")
            archive_dir = os.path.join(tmp_dir, "archive")
            
            dest_path = archive_source_file(source_file, archive_dir)
            self.assertFalse(os.path.exists(source_file))
            self.assertTrue(os.path.exists(dest_path))
            self.assertEqual(dest_path, os.path.join(archive_dir, "book.cbz"))

    def test_archive_source_file_collision(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_file = os.path.join(tmp_dir, "book.cbz")
            with open(source_file, "w") as f:
                f.write("dummy new content")
            archive_dir = os.path.join(tmp_dir, "archive")
            os.makedirs(archive_dir, exist_ok=True)
            existing_file = os.path.join(archive_dir, "book.cbz")
            with open(existing_file, "w") as f:
                f.write("dummy existing content")
            
            dest_path = archive_source_file(source_file, archive_dir)
            self.assertFalse(os.path.exists(source_file))
            self.assertTrue(os.path.exists(existing_file))
            self.assertTrue(os.path.exists(dest_path))
            self.assertNotEqual(dest_path, existing_file)
            self.assertIn("book_", os.path.basename(dest_path))

    def test_archive_source_file_unsafe_path(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_file = os.path.join(tmp_dir, "book.cbz")
            with open(source_file, "w") as f:
                f.write("dummy")
            unsafe_dir = os.path.join(tmp_dir, "..", "outside_archive")
            with self.assertRaises(ValueError):
                archive_source_file(source_file, unsafe_dir, base_dir=tmp_dir)

    def test_process_books_archiving(self):
        import tempfile
        from PIL import Image
        import io
        from parser import process_books

        with tempfile.TemporaryDirectory() as tmp_dir:
            source_dir = os.path.join(tmp_dir, "source")
            output_dir = os.path.join(tmp_dir, "output")
            archive_dir = os.path.join(tmp_dir, "archive")
            os.makedirs(source_dir)
            os.makedirs(output_dir)

            img = Image.new('RGB', (1, 1), color='red')
            buf = io.BytesIO()
            img.save(buf, format='JPEG')
            jpg_bytes = buf.getvalue()

            # Valid book
            valid_path = os.path.join(source_dir, "Valid Book.cbz")
            with zipfile.ZipFile(valid_path, 'w') as z:
                z.writestr("1.jpg", jpg_bytes)

            # Corrupt book
            corrupt_path = os.path.join(source_dir, "Corrupt Book.cbz")
            with open(corrupt_path, 'w') as f:
                f.write("not a zip")

            summary = process_books(source_dir, output_dir, archive_dir=archive_dir)

            # Valid book should be archived, corrupt book should stay in source
            self.assertFalse(os.path.exists(valid_path))
            self.assertTrue(os.path.exists(os.path.join(archive_dir, "Valid Book.cbz")))
            self.assertTrue(os.path.exists(corrupt_path))

            self.assertEqual(summary["total_found"], 2)
            self.assertEqual(summary["successfully_parsed"], 1)
            self.assertEqual(summary["archived"], 1)
            self.assertEqual(summary["failed"], 1)

    def test_load_toc_data_internal(self):
        import tempfile
        import json
        with tempfile.TemporaryDirectory() as tmp_dir:
            archive_path = os.path.join(tmp_dir, "book.cbz")
            toc_content = {
                "title": "Table of Contents",
                "chapters": [
                    {"id": "c001", "chapter": "CH 1", "start_page": 1, "end_page": 2},
                    {"id": "c002", "chapter": "CH 2", "start_page": 3, "end_page": 4}
                ]
            }
            with zipfile.ZipFile(archive_path, 'w') as z:
                z.writestr("toc.json", json.dumps(toc_content))
                z.writestr("1.jpg", b"fake")

            with zipfile.ZipFile(archive_path, 'r') as z:
                toc_data, raw_str = load_toc_data(archive_path, z)
                self.assertIsNotNone(toc_data)
                self.assertEqual(len(toc_data["chapters"]), 2)
                self.assertEqual(toc_data["chapters"][0]["id"], "c001")

    def test_load_toc_data_external(self):
        import tempfile
        import json
        with tempfile.TemporaryDirectory() as tmp_dir:
            archive_path = os.path.join(tmp_dir, "book.cbz")
            toc_path = os.path.join(tmp_dir, "book.toc.json")
            toc_content = {
                "title": "Table of Contents",
                "chapters": [
                    {"id": "c001", "chapter": "CH 1", "start_page": 1, "end_page": 5}
                ]
            }
            with open(toc_path, 'w', encoding='utf-8') as f:
                json.dump(toc_content, f)

            with zipfile.ZipFile(archive_path, 'w') as z:
                z.writestr("1.jpg", b"fake")

            with zipfile.ZipFile(archive_path, 'r') as z:
                toc_data, raw_str = load_toc_data(archive_path, z)
                self.assertIsNotNone(toc_data)
                self.assertEqual(toc_data["chapters"][0]["id"], "c001")

    def test_process_book_with_internal_toc_json(self):
        import tempfile
        import json
        from PIL import Image
        import io
        from parser import process_books

        with tempfile.TemporaryDirectory() as tmp_dir:
            source_dir = os.path.join(tmp_dir, "source")
            output_dir = os.path.join(tmp_dir, "output")
            os.makedirs(source_dir)
            os.makedirs(output_dir)

            img = Image.new('RGB', (1, 1), color='blue')
            buf = io.BytesIO()
            img.save(buf, format='JPEG')
            jpg_bytes = buf.getvalue()

            toc_content = {
                "title": "Table of Contents",
                "chapters": [
                    {"id": "c001", "chapter": "CH 1", "title": "Chapter One", "start_page": 1, "end_page": 2},
                    {"id": "c002", "chapter": "CH 2", "title": "Chapter Two", "start_page": 3, "end_page": 4}
                ]
            }

            book_path = os.path.join(source_dir, "TOC Book.cbz")
            with zipfile.ZipFile(book_path, 'w') as z:
                z.writestr("toc.json", json.dumps(toc_content))
                z.writestr("page1.jpg", jpg_bytes)
                z.writestr("page2.jpg", jpg_bytes)
                z.writestr("page3.jpg", jpg_bytes)
                z.writestr("page4.jpg", jpg_bytes)

            summary = process_books(source_dir, output_dir, archive_dir="")
            self.assertEqual(summary["successfully_parsed"], 1)

            book_dir = os.path.join(output_dir, "local", "TOC Book")
            self.assertTrue(os.path.exists(os.path.join(book_dir, "chapter_1")))
            self.assertTrue(os.path.exists(os.path.join(book_dir, "chapter_2")))
            self.assertTrue(os.path.exists(os.path.join(book_dir, "toc.json")))

            ch1_files = os.listdir(os.path.join(book_dir, "chapter_1"))
            ch2_files = os.listdir(os.path.join(book_dir, "chapter_2"))
            self.assertEqual(len(ch1_files), 2)
            self.assertEqual(len(ch2_files), 2)

    def test_process_book_with_invalid_toc_json_fallback(self):
        import tempfile
        from PIL import Image
        import io
        from parser import process_books

        with tempfile.TemporaryDirectory() as tmp_dir:
            source_dir = os.path.join(tmp_dir, "source")
            output_dir = os.path.join(tmp_dir, "output")
            os.makedirs(source_dir)
            os.makedirs(output_dir)

            img = Image.new('RGB', (1, 1), color='green')
            buf = io.BytesIO()
            img.save(buf, format='JPEG')
            jpg_bytes = buf.getvalue()

            book_path = os.path.join(source_dir, "Invalid TOC Book.cbz")
            with zipfile.ZipFile(book_path, 'w') as z:
                z.writestr("toc.json", "INVALID { JSON")
                z.writestr("Invalid TOC Book - c001 - p001.jpg", jpg_bytes)

            summary = process_books(source_dir, output_dir, archive_dir="")
            self.assertEqual(summary["successfully_parsed"], 1)

            book_dir = os.path.join(output_dir, "local", "Invalid TOC Book")
            self.assertTrue(os.path.exists(os.path.join(book_dir, "chapter_1")))

    def test_group_pages_by_toc_outliers(self):
        import tempfile
        import json
        from PIL import Image
        import io
        from parser import process_books

        with tempfile.TemporaryDirectory() as tmp_dir:
            source_dir = os.path.join(tmp_dir, "source")
            output_dir = os.path.join(tmp_dir, "output")
            os.makedirs(source_dir)
            os.makedirs(output_dir)

            img = Image.new('RGB', (1, 1), color='purple')
            buf = io.BytesIO()
            img.save(buf, format='JPEG')
            jpg_bytes = buf.getvalue()

            toc_content = {
                "title": "Table of Contents",
                "chapters": [
                    {"id": "c001", "chapter": "CH 1", "start_page": 3, "end_page": 4},
                    {"id": "c002", "chapter": "CH 2", "start_page": 5, "end_page": 6}
                ]
            }

            book_path = os.path.join(source_dir, "Outlier TOC Book.cbz")
            with zipfile.ZipFile(book_path, 'w') as z:
                z.writestr("toc.json", json.dumps(toc_content))
                z.writestr("p001.jpg", jpg_bytes)
                z.writestr("p002.jpg", jpg_bytes)
                z.writestr("p003.jpg", jpg_bytes)
                z.writestr("p004.jpg", jpg_bytes)
                z.writestr("p005.jpg", jpg_bytes)
                z.writestr("p006.jpg", jpg_bytes)
                z.writestr("p007.jpg", jpg_bytes)
                z.writestr("p008.jpg", jpg_bytes)

            summary = process_books(source_dir, output_dir, archive_dir="")
            self.assertEqual(summary["successfully_parsed"], 1)

            book_dir = os.path.join(output_dir, "local", "Outlier TOC Book")
            self.assertTrue(os.path.exists(os.path.join(book_dir, "chapter_0")), "chapter_0 must exist for pages 1-2")
            self.assertTrue(os.path.exists(os.path.join(book_dir, "chapter_1")), "chapter_1 must exist for pages 3-4")
            self.assertTrue(os.path.exists(os.path.join(book_dir, "chapter_2")), "chapter_2 must exist for pages 5-6")
            self.assertTrue(os.path.exists(os.path.join(book_dir, "chapter_2_extra_1")), "chapter_2_extra_1 must exist for trailing pages 7-8")

            ch0_files = os.listdir(os.path.join(book_dir, "chapter_0"))
            ch1_files = os.listdir(os.path.join(book_dir, "chapter_1"))
            ch2_files = os.listdir(os.path.join(book_dir, "chapter_2"))
            extra_files = os.listdir(os.path.join(book_dir, "chapter_2_extra_1"))

            self.assertEqual(len(ch0_files), 2)
            self.assertEqual(len(ch1_files), 2)
            self.assertEqual(len(ch2_files), 2)
            self.assertEqual(len(extra_files), 2)

    def test_group_pages_by_toc_named_sections(self):
        from parser import group_pages_by_toc, PageInfo
        pages = [PageInfo(name=f"p{i:03d}.jpg", chapter=None, page=i, is_cover=False) for i in range(1, 13)]
        toc_data = {
            "title": "Book with named sections",
            "chapters": [
                {"id": "c001", "chapter": "CH 1", "start_page": 3, "end_page": 4},
                {"id": "c002", "chapter": "CH 2", "start_page": 5, "end_page": 6},
                {"id": "finale", "chapter": "Finale", "start_page": 7, "end_page": 8},
                {"id": "appendix", "chapter": "Appendix", "start_page": 9, "end_page": 10}
            ]
        }

        groups = group_pages_by_toc(pages, toc_data)
        self.assertIn("c000", groups)
        self.assertIn("c001", groups)
        self.assertIn("c002", groups)
        self.assertIn("c003", groups)
        self.assertIn("c004", groups)
        self.assertIn("c004x1", groups)

        self.assertEqual([p.name for p in groups["c000"]], ["p001.jpg", "p002.jpg"])
        self.assertEqual([p.name for p in groups["c001"]], ["p003.jpg", "p004.jpg"])
        self.assertEqual([p.name for p in groups["c002"]], ["p005.jpg", "p006.jpg"])
        self.assertEqual([p.name for p in groups["c003"]], ["p007.jpg", "p008.jpg"])
        self.assertEqual([p.name for p in groups["c004"]], ["p009.jpg", "p010.jpg"])
        self.assertEqual([p.name for p in groups["c004x1"]], ["p011.jpg", "p012.jpg"])

    def test_safe_join(self):
        from parser import _safe_join
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            # Valid path inside base
            safe_path = _safe_join(tmp_dir, "subfolder", "file.txt")
            self.assertTrue(safe_path.startswith(os.path.realpath(tmp_dir)))
            self.assertTrue(safe_path.endswith("file.txt"))

            # Traversal attempt should raise ValueError
            with self.assertRaises(ValueError):
                _safe_join(tmp_dir, "..", "outside.txt")

    def test_sanitize_folder_name_reserved(self):
        self.assertEqual(sanitize_folder_name("CON"), "_CON_")
        self.assertEqual(sanitize_folder_name("aux.txt"), "_aux.txt_")
        self.assertEqual(sanitize_folder_name("Book Name."), "Book Name_")
        self.assertEqual(sanitize_folder_name("  Book Name  "), "Book Name")

    def test_load_toc_data_oversized_internal(self):
        import tempfile
        import parser
        with tempfile.TemporaryDirectory() as tmp_dir:
            archive_path = os.path.join(tmp_dir, "book.cbz")
            with zipfile.ZipFile(archive_path, 'w') as z:
                z.writestr("toc.json", '{"chapters": []}')

            old_max = parser.MAX_FILE_SIZE
            parser.MAX_FILE_SIZE = 5  # bytes
            try:
                with zipfile.ZipFile(archive_path, 'r') as z:
                    toc_data, raw_str = load_toc_data(archive_path, z)
                    self.assertIsNone(toc_data)
                    self.assertEqual(raw_str, "")
            finally:
                parser.MAX_FILE_SIZE = old_max

    def test_load_toc_data_system_dir_ignore(self):
        import tempfile
        import json
        with tempfile.TemporaryDirectory() as tmp_dir:
            archive_path = os.path.join(tmp_dir, "book.cbz")
            with zipfile.ZipFile(archive_path, 'w') as z:
                z.writestr("__MACOSX/toc.json", json.dumps({"chapters": [{"id": "c001"}]}))
                z.writestr(".hidden/toc.json", json.dumps({"chapters": [{"id": "c002"}]}))

            with zipfile.ZipFile(archive_path, 'r') as z:
                toc_data, raw_str = load_toc_data(archive_path, z)
                self.assertIsNone(toc_data)

    def test_archive_reader_zip(self):
        import tempfile
        from parser import ArchiveReader
        with tempfile.TemporaryDirectory() as tmp_dir:
            archive_path = os.path.join(tmp_dir, "test.zip")
            with zipfile.ZipFile(archive_path, 'w') as z:
                z.writestr("test.txt", "hello world")

            self.assertTrue(ArchiveReader.is_archive(archive_path))
            with ArchiveReader(archive_path) as reader:
                self.assertEqual(reader.archive_type, "zip")
                infolist = reader.infolist()
                self.assertEqual(len(infolist), 1)
                self.assertEqual(infolist[0].filename, "test.txt")
                self.assertFalse(infolist[0].is_dir())
                self.assertEqual(reader.read("test.txt"), b"hello world")

    def test_process_books_rar_discovery_without_rarfile(self):
        import tempfile
        from parser import process_books
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_dir = os.path.join(tmp_dir, "source")
            output_dir = os.path.join(tmp_dir, "output")
            os.makedirs(source_dir)
            os.makedirs(output_dir)

            # Create a dummy .rar file
            rar_path = os.path.join(source_dir, "Book.rar")
            with open(rar_path, "wb") as f:
                f.write(b"Rar!\x1a\x07\x00not_a_real_rar")

            summary = process_books(source_dir, output_dir, archive_dir="")
            self.assertEqual(summary["total_found"], 1)
            self.assertEqual(summary["successfully_parsed"], 0)
            self.assertEqual(summary["failed"], 1)

    def test_archive_reader_mocked_rarfile(self):
        import tempfile
        from unittest.mock import patch, MagicMock
        import parser
        from parser import process_single_book

        with tempfile.TemporaryDirectory() as tmp_dir:
            rar_path = os.path.join(tmp_dir, "RarBook.rar")
            with open(rar_path, "wb") as f:
                f.write(b"Rar!\x1a\x07\x00dummy")

            # Mock rarfile module behavior
            mock_rarfile_mod = MagicMock()
            mock_rarfile_mod.is_rarfile.return_value = True

            mock_info_cover = MagicMock(filename="RarBook - c001 - p000 [Cover].jpg", file_size=10)
            mock_info_cover.isdir.return_value = False
            mock_info_cover.is_dir.return_value = False

            mock_info_page = MagicMock(filename="RarBook - c001 - p001.jpg", file_size=10)
            mock_info_page.isdir.return_value = False
            mock_info_page.is_dir.return_value = False

            mock_rf_instance = MagicMock()
            mock_rf_instance.infolist.return_value = [mock_info_cover, mock_info_page]

            # 1x1 RED image bytes
            from PIL import Image
            import io
            img = Image.new('RGB', (1, 1), color='red')
            buf = io.BytesIO()
            img.save(buf, format='JPEG')
            img_bytes = buf.getvalue()

            def mock_open(name):
                return io.BytesIO(img_bytes)

            mock_rf_instance.open.side_effect = mock_open
            mock_rarfile_mod.RarFile.return_value = mock_rf_instance

            with patch.object(parser, 'rarfile', mock_rarfile_mod), patch.object(parser, 'HAS_RARFILE', True):
                output_dir = os.path.join(tmp_dir, "output")
                success = process_single_book(rar_path, output_dir)
                self.assertTrue(success)

                book_dir = os.path.join(output_dir, "local", "RarBook")
                self.assertTrue(os.path.exists(os.path.join(book_dir, "cover.jpg")))
                self.assertTrue(os.path.exists(os.path.join(book_dir, "chapter_1", "image_1.jpg")))

    def test_rarfile_missing_unrar_cli_tool(self):
        import tempfile
        from unittest.mock import patch, MagicMock
        import parser
        from parser import process_single_book

        class MockRarCannotExec(Exception):
            pass

        with tempfile.TemporaryDirectory() as tmp_dir:
            rar_path = os.path.join(tmp_dir, "RarBook.rar")
            with open(rar_path, "wb") as f:
                f.write(b"Rar!\x1a\x07\x00dummy")

            mock_rarfile_mod = MagicMock()
            mock_rarfile_mod.is_rarfile.return_value = True
            mock_rarfile_mod.RarCannotExec = MockRarCannotExec
            mock_rarfile_mod.Error = Exception

            mock_info_cover = MagicMock(filename="RarBook - c001 - p000 [Cover].jpg", file_size=10)
            mock_info_cover.isdir.return_value = False
            mock_info_cover.is_dir.return_value = False

            mock_rf_instance = MagicMock()
            mock_rf_instance.infolist.return_value = [mock_info_cover]
            mock_rf_instance.read.side_effect = MockRarCannotExec("Cannot find working tool")

            mock_rarfile_mod.RarFile.return_value = mock_rf_instance

            with patch.object(parser, 'rarfile', mock_rarfile_mod), patch.object(parser, 'HAS_RARFILE', True):
                output_dir = os.path.join(tmp_dir, "output")
                success = process_single_book(rar_path, output_dir)
                self.assertFalse(success)


if __name__ == "__main__":
    unittest.main()







