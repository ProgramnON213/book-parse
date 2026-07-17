import os
import re
import zipfile
import argparse
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass
from PIL import Image

@dataclass
class PageInfo:
    name: str
    chapter: str
    page: int
    is_cover: bool

# Pre-compiled regular expressions for parsing chapter IDs and page info
CHAPTER_PATTERN_PREFER = re.compile(r' - (c\d+(?:x\d+)?)\b')
CHAPTER_PATTERN_FALLBACK = re.compile(r'\b(c\d+(?:x\d+)?)\b')
PAGE_PATTERN_PREFER = re.compile(r' - p(\d+)')
PAGE_PATTERN_FALLBACK = re.compile(r'\bp(\d+)')
NATURAL_SORT_PATTERN = re.compile(r'^c(\d+)(?:x(\d+))?$')

def sanitize_folder_name(name: str) -> str:
    """
    Sanitizes a string to make it safe for directory names by replacing invalid characters.
    """
    return re.sub(r'[\\/*?:"<>|]', '_', name)

# Security constraints to prevent Denial of Service (DoS) / Zip Bomb attacks
MAX_FILE_SIZE = 100 * 1024 * 1024  # Max size for individual extracted files (100 MB)
MAX_BOOK_UNCOMPRESSED_SIZE = 1024 * 1024 * 1024  # Max total uncompressed size for a book archive (1 GB)

def check_safe_path(base_dir: str, target_path: str) -> bool:
    """
    Verifies that target_path is strictly inside base_dir to prevent directory traversal.
    """
    abs_base = os.path.abspath(base_dir)
    abs_target = os.path.abspath(target_path)
    return os.path.commonpath([abs_base, abs_target]) == abs_base

def extract_chapter_id(filename: str) -> str:
    """
    Extracts chapter identifier (e.g. 'c001', 'c005x1') from a page filename.
    """
    match = CHAPTER_PATTERN_PREFER.search(filename)
    if match:
        return match.group(1)
    
    match = CHAPTER_PATTERN_FALLBACK.search(filename)
    if match:
        return match.group(1)
    
    return ""

def extract_page_info(filename: str) -> int:
    """
    Extracts the page starting index (e.g. 'p001' -> 1, 'p174-p175' -> 174) from a page filename.
    """
    match = PAGE_PATTERN_PREFER.search(filename)
    if match:
        return int(match.group(1))
    
    match = PAGE_PATTERN_FALLBACK.search(filename)
    if match:
        return int(match.group(1))
    
    return 0

def natural_chapter_sort_key(chapter_id: str) -> Tuple[int, int]:
    """
    Parses a chapter ID (e.g. 'c005x1') into a tuple for sorting: (chapter_num, extra_num).
    """
    match = NATURAL_SORT_PATTERN.match(chapter_id)
    if match:
        chapter_num = int(match.group(1))
        extra_num = int(match.group(2)) if match.group(2) else 0
        return (chapter_num, extra_num)
    return (9999, 9999)

def is_cover_image(filename: str) -> bool:
    """
    Determines if a page filename represents a cover image.
    """
    return "[Cover]" in filename or "p000" in filename

def format_chapter_folder_name(chapter_id: str) -> str:
    """
    Formats the chapter folder name based on the chapter ID.
    e.g. 'c001' -> 'chapter_1', 'c005x1' -> 'chapter_5_extra_1'.
    """
    chapter_num, extra_num = natural_chapter_sort_key(chapter_id)
    if extra_num > 0:
        return f"chapter_{chapter_num}_extra_{extra_num}"
    return f"chapter_{chapter_num}"

def process_books(source_dir: str, output_dir: str) -> None:
    """
    Processes all CBR books in the source directory and organizes them into output folder.
    Each book is parsed independently and placed inside a folder named after its CBR filename.
    """
    if not os.path.exists(source_dir):
        print(f"Source directory '{source_dir}' does not exist.")
        return

    cbr_files = sorted([f for f in os.listdir(source_dir) if f.endswith('.cbr')])
    if not cbr_files:
        print(f"No .cbr files found in '{source_dir}'.")
        return

    print(f"Found {len(cbr_files)} books to process.")

    for file_name in cbr_files:
        archive_path = os.path.join(source_dir, file_name)
        book_folder_name = sanitize_folder_name(os.path.splitext(file_name)[0])
        print(f"\nProcessing book: '{file_name}'")

        if not zipfile.is_zipfile(archive_path):
            print(f"Warning: '{file_name}' is not a valid zip archive (CBR). Skipping.")
            continue

        book_dir = os.path.join(output_dir, "local", book_folder_name)
        if not check_safe_path(output_dir, book_dir):
            print(f"Warning: '{file_name}' resolves to an invalid path outside of '{output_dir}'. Skipping.")
            continue

        os.makedirs(book_dir, exist_ok=True)
        print(f"Output directory: {book_dir}")

        try:
            pages: List[PageInfo] = []
            with zipfile.ZipFile(archive_path, 'r') as z:
                # Security: Check decompression size limits (Zip Bomb prevention)
                total_uncompressed_size = 0
                for info in z.infolist():
                    if info.file_size > MAX_FILE_SIZE:
                        raise ValueError(f"Archive member '{info.filename}' size ({info.file_size} B) exceeds maximum allowed size ({MAX_FILE_SIZE} B).")
                    total_uncompressed_size += info.file_size
                
                if total_uncompressed_size > MAX_BOOK_UNCOMPRESSED_SIZE:
                    raise ValueError(f"Archive total uncompressed size ({total_uncompressed_size} B) exceeds maximum allowed size ({MAX_BOOK_UNCOMPRESSED_SIZE} B).")

                for name in z.namelist():
                    # We only care about webp image files
                    if name.lower().endswith('.webp'):
                        base_name = os.path.basename(name)
                        chap_id = extract_chapter_id(base_name)
                        page_num = extract_page_info(base_name)
                        is_cov = is_cover_image(base_name)

                        pages.append(PageInfo(
                            name=name,
                            chapter=chap_id,
                            page=page_num,
                            is_cover=is_cov
                        ))

                if not pages:
                    print("Warning: No webp pages found in this book.")
                    continue

                # 1. Handle Cover Page
                cover_page = None
                for p in pages:
                    if p.is_cover:
                        cover_page = p
                        break
                
                if not cover_page:
                    cover_page = min(pages, key=lambda x: x.name)

                print(f"Generating cover from: {os.path.basename(cover_page.name)}")
                try:
                    cover_path = os.path.join(book_dir, "cover.jpg")
                    if not check_safe_path(book_dir, cover_path):
                        raise ValueError(f"Target cover path '{cover_path}' is outside book directory '{book_dir}'.")
                    with z.open(cover_page.name) as zf:
                        with Image.open(zf) as img:
                            # Convert to RGB (required for saving as JPEG)
                            rgb_img = img.convert('RGB')
                            rgb_img.save(cover_path, "JPEG")
                except Exception as e:
                    print(f"Error converting cover image: {e}")

                # 2. Group and process pages by chapter
                chapter_groups: Dict[str, List[PageInfo]] = {}
                for p in pages:
                    chap_id = p.chapter
                    if not chap_id:
                        chap_id = "c000"
                    if chap_id not in chapter_groups:
                        chapter_groups[chap_id] = []
                    chapter_groups[chap_id].append(p)

                # Sort chapter IDs naturally
                sorted_chapter_ids = sorted(chapter_groups.keys(), key=natural_chapter_sort_key)

                for chap_id in sorted_chapter_ids:
                    chapter_pages = chapter_groups[chap_id]
                    # Sort pages numerically by page index
                    sorted_pages = sorted(chapter_pages, key=lambda x: x.page)

                    chapter_folder_name = format_chapter_folder_name(chap_id)
                    chapter_dir = os.path.join(book_dir, chapter_folder_name)
                    if not check_safe_path(book_dir, chapter_dir):
                        raise ValueError(f"Chapter directory '{chapter_dir}' is outside book directory '{book_dir}'.")
                    os.makedirs(chapter_dir, exist_ok=True)

                    print(f"  Writing {chapter_folder_name} ({len(sorted_pages)} pages)...")

                    for i, p in enumerate(sorted_pages, start=1):
                        dest_file_name = f"image_{i}.webp"
                        dest_path = os.path.join(chapter_dir, dest_file_name)
                        if not check_safe_path(chapter_dir, dest_path):
                            raise ValueError(f"Destination path '{dest_path}' is outside chapter directory '{chapter_dir}'.")

                        data = z.read(p.name)
                        with open(dest_path, 'wb') as df:
                            df.write(data)
        except zipfile.BadZipFile as e:
            print(f"Error: '{file_name}' is a corrupted zip archive: {e}. Skipping.")
        except Exception as e:
            print(f"Error processing book '{file_name}': {e}. Skipping.")

    print("\nProcessing complete!")

def main() -> None:
    parser = argparse.ArgumentParser(description="Parse CBR books into organized chapters.")
    parser.add_argument("--source", default="./source", help="Source directory containing .cbr files")
    parser.add_argument("--output", default="./output", help="Output directory to place parsed structure")
    args = parser.parse_args()

    process_books(args.source, args.output)

if __name__ == "__main__":
    main()
