import os
import re
import zipfile
import argparse
import shutil
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass
from collections import defaultdict
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
    Resolves symbolic links and handles different drives on Windows safely.
    """
    abs_base = os.path.realpath(base_dir)
    abs_target = os.path.realpath(target_path)
    try:
        return os.path.commonpath([abs_base, abs_target]) == abs_base
    except ValueError:
        return False

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

def process_single_book(archive_path: str, output_dir: str) -> None:
    """
    Processes a single CBR/CBZ book archive.
    """
    file_name = os.path.basename(archive_path)
    book_folder_name = sanitize_folder_name(os.path.splitext(file_name)[0])

    try:
        if not zipfile.is_zipfile(archive_path):
            print(f"Warning: '{file_name}' is not a valid zip archive (CBR/CBZ). Skipping.")
            return

        book_dir = os.path.join(output_dir, "local", book_folder_name)
        if not check_safe_path(output_dir, book_dir):
            print(f"Warning: '{file_name}' resolves to an invalid path outside of '{output_dir}'. Skipping.")
            return

        pages: List[PageInfo] = []
        with zipfile.ZipFile(archive_path, 'r') as z:
            # Security: Check decompression size limits (Zip Bomb prevention) and filter pages in one pass
            total_uncompressed_size = 0
            for info in z.infolist():
                if info.file_size > MAX_FILE_SIZE:
                    raise ValueError(f"Archive member '{info.filename}' size ({info.file_size} B) exceeds maximum allowed size ({MAX_FILE_SIZE} B).")
                total_uncompressed_size += info.file_size
                
                # We care about webp, jpg, jpeg, and png image files
                if info.filename.lower().endswith(('.webp', '.jpg', '.jpeg', '.png')):
                    base_name = os.path.basename(info.filename)
                    pages.append(PageInfo(
                        name=info.filename,
                        chapter=extract_chapter_id(base_name),
                        page=extract_page_info(base_name),
                        is_cover=is_cover_image(base_name)
                    ))
            
            if total_uncompressed_size > MAX_BOOK_UNCOMPRESSED_SIZE:
                raise ValueError(f"Archive total uncompressed size ({total_uncompressed_size} B) exceeds maximum allowed size ({MAX_BOOK_UNCOMPRESSED_SIZE} B).")

            if not pages:
                print("Warning: No matching image pages found in this book.")
                return

            # Create book directory only when we know we have valid pages to write
            os.makedirs(book_dir, exist_ok=True)
            print(f"Output directory: {book_dir}")

            # 1. Handle Cover Page
            cover_page = next((p for p in pages if p.is_cover), min(pages, key=lambda x: x.name))

            print(f"Generating cover from: {os.path.basename(cover_page.name)}")
            try:
                cover_path = os.path.join(book_dir, "cover.jpg")
                if not check_safe_path(book_dir, cover_path):
                    raise ValueError(f"Target cover path '{cover_path}' is outside book directory '{book_dir}'.")
                with z.open(cover_page.name) as zf:
                    with Image.open(zf) as img:
                        # Handle transparency for PNG/WebP cover images
                        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            background.paste(img, mask=img.split()[-1])
                            rgb_img = background
                        else:
                            rgb_img = img.convert('RGB')
                        rgb_img.save(cover_path, "JPEG")
            except Exception as e:
                print(f"Error converting cover image: {e}")

            # 2. Group and process pages by chapter
            chapter_groups = defaultdict(list)
            for p in pages:
                chap_id = p.chapter or "c000"
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
                    ext = os.path.splitext(p.name)[1].lower()
                    dest_file_name = f"image_{i}{ext}"
                    dest_path = os.path.join(chapter_dir, dest_file_name)
                    if not check_safe_path(chapter_dir, dest_path):
                        raise ValueError(f"Destination path '{dest_path}' is outside chapter directory '{chapter_dir}'.")

                    # Stream the file content directly to target to optimize memory
                    with z.open(p.name) as source, open(dest_path, 'wb') as target:
                        shutil.copyfileobj(source, target)
    except zipfile.BadZipFile as e:
        print(f"Error: '{file_name}' is a corrupted zip archive: {e}. Skipping.")
    except Exception as e:
        print(f"Error processing book '{file_name}': {e}. Skipping.")

def process_books(source_dir: str, output_dir: str) -> None:
    """
    Processes all CBR and CBZ books in the source directory and organizes them into output folder.
    """
    if not os.path.exists(source_dir):
        print(f"Source directory '{source_dir}' does not exist.")
        return

    book_files = sorted([f for f in os.listdir(source_dir) if f.lower().endswith(('.cbr', '.cbz'))])
    if not book_files:
        print(f"No .cbr or .cbz files found in '{source_dir}'.")
        return

    print(f"Found {len(book_files)} books to process.")

    for file_name in book_files:
        archive_path = os.path.join(source_dir, file_name)
        print(f"\nProcessing book: '{file_name}'")
        process_single_book(archive_path, output_dir)

    print("\nProcessing complete!")

def main() -> None:
    parser = argparse.ArgumentParser(description="Parse CBR/CBZ books into organized chapters.")
    parser.add_argument("--source", default="./source", help="Source directory containing .cbr or .cbz files")
    parser.add_argument("--output", default="./output", help="Output directory to place parsed structure")
    args = parser.parse_args()

    process_books(args.source, args.output)

if __name__ == "__main__":
    main()
