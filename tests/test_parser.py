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

if __name__ == "__main__":
    unittest.main()
