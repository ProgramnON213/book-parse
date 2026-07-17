import os
import zipfile
import unittest
from parser import (
    extract_series_title,
    extract_chapter_id,
    extract_page_info,
    natural_chapter_sort_key,
    is_cover_image,
)

class TestParser(unittest.TestCase):
    def test_extract_series_title(self):
        filenames = [
            "Betrayed by the Hero, I Formed a MILF Party With His Mom! v01 (2025) (Digital) (kaOak) (f) optimized_webp_q75.cbr",
            "Betrayed by the Hero, I Formed a MILF Party With His Mom! v02 (2025) (Digital) (kaOak) optimized_webp_q75.cbr",
            "Betrayed by the Hero, I Formed a MILF Party With His Mom! v03 (2025) (Digital) (kaOak) optimized_webp_q75.cbr",
            "Betrayed by the Hero, I Formed a MILF Party With His Mom! v04 (2026) (Digital) (kaOak) optimized_webp_q75.cbr",
        ]
        expected = "Betrayed by the Hero, I Formed a MILF Party With His Mom!"
        for name in filenames:
            self.assertEqual(extract_series_title(name), expected)

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
            process_books(source_dir, output_dir)

            # Check that the outputs were created correctly
            series_dir = os.path.join(output_dir, "local", "Test Book")
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


if __name__ == "__main__":
    unittest.main()

