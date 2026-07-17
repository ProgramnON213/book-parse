import os
import re
import zipfile
import argparse
from typing import List, Tuple, Dict, Any
from PIL import Image

def extract_series_title(filename: str) -> str:
    """
    Extracts the series title from the CBR filename.
    Matches everything before the volume signifier (e.g. ' v01', ' Vol.1', ' Vol 1').
    """
    name_no_ext = os.path.splitext(filename)[0]
    match = re.search(r'^(.*?)\s+(?:v\d+|Vol\.\d+|Vol\s+\d+|v[oO]l\.\d+)\b', name_no_ext)
    if match:
        return match.group(1).strip()
    
    # Fallback: strip standard bracketed/parenthesized tags at the end
    clean_name = re.sub(r'\s*[\(\[\{].*$', '', name_no_ext)
    return clean_name.strip()

def extract_chapter_id(filename: str) -> str:
    """
    Extracts chapter identifier (e.g. 'c001', 'c005x1') from a page filename.
    """
    match = re.search(r' - (c\d+(?:x\d+)?)\b', filename)
    if match:
        return match.group(1)
    
    match = re.search(r'\b(c\d+(?:x\d+)?)\b', filename)
    if match:
        return match.group(1)
    
    return ""

def extract_page_info(filename: str) -> int:
    """
    Extracts the page starting index (e.g. 'p001' -> 1, 'p174-p175' -> 174) from a page filename.
    """
    match = re.search(r' - p(\d+)', filename)
    if match:
        return int(match.group(1))
    
    match = re.search(r'\bp(\d+)', filename)
    if match:
        return int(match.group(1))
    
    return 0

def natural_chapter_sort_key(chapter_id: str) -> Tuple[int, int]:
    """
    Parses a chapter ID (e.g. 'c005x1') into a tuple for sorting: (chapter_num, extra_num).
    """
    match = re.match(r'^c(\d+)(?:x(\d+))?$', chapter_id)
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
    """
    if not os.path.exists(source_dir):
        print(f"Source directory '{source_dir}' does not exist.")
        return

    cbr_files = sorted([f for f in os.listdir(source_dir) if f.endswith('.cbr')])
    if not cbr_files:
        print(f"No .cbr files found in '{source_dir}'.")
        return

    print(f"Found {len(cbr_files)} books to process.")

    # Group all pages across all books by series title
    # Structure: { series_title: [ { 'archive': path, 'name': name, 'chapter': id, 'page': num, 'is_cover': bool } ] }
    series_pages: Dict[str, List[Dict[str, Any]]] = {}

    for file_name in cbr_files:
        archive_path = os.path.join(source_dir, file_name)
        series_title = extract_series_title(file_name)
        print(f"Reading '{file_name}' -> Series: '{series_title}'")

        if not zipfile.is_zipfile(archive_path):
            print(f"Warning: '{file_name}' is not a valid zip archive (CBR). Skipping.")
            continue

        if series_title not in series_pages:
            series_pages[series_title] = []

        with zipfile.ZipFile(archive_path, 'r') as z:
            for name in z.namelist():
                # We only care about webp image files
                if name.lower().endswith('.webp'):
                    chap_id = extract_chapter_id(name)
                    page_num = extract_page_info(name)
                    is_cov = is_cover_image(name)

                    series_pages[series_title].append({
                        'archive': archive_path,
                        'name': name,
                        'chapter': chap_id,
                        'page': page_num,
                        'is_cover': is_cov
                    })

    # Process each series
    for series_title, pages in series_pages.items():
        print(f"\nProcessing series: '{series_title}'")
        
        # Create series directory structure
        series_dir = os.path.join(output_dir, "local", series_title)
        os.makedirs(series_dir, exist_ok=True)
        print(f"Output directory: {series_dir}")

        # 1. Handle Cover Page
        cover_page = None
        # Try to find a page flagged as cover first
        for p in pages:
            if p['is_cover']:
                cover_page = p
                break
        
        # Fallback to the first page alphabetically if no cover tag is found
        if not cover_page and pages:
            cover_page = min(pages, key=lambda x: x['name'])

        if cover_page:
            print(f"Generating cover from: {os.path.basename(cover_page['name'])}")
            with zipfile.ZipFile(cover_page['archive'], 'r') as z:
                with z.open(cover_page['name']) as zf:
                    try:
                        with Image.open(zf) as img:
                            # Convert to RGB (required for saving as JPEG)
                            rgb_img = img.convert('RGB')
                            cover_path = os.path.join(series_dir, "cover.jpg")
                            rgb_img.save(cover_path, "JPEG")
                    except Exception as e:
                        print(f"Error converting cover image: {e}")
        else:
            print("Warning: No pages found to generate cover.")

        # 2. Group and process pages by chapter
        chapter_groups: Dict[str, List[Dict[str, Any]]] = {}
        for p in pages:
            chap_id = p['chapter']
            if not chap_id:
                # If we couldn't extract a chapter ID, place in a default folder or ignore
                chap_id = "c000"
            if chap_id not in chapter_groups:
                chapter_groups[chap_id] = []
            chapter_groups[chap_id].append(p)

        # Sort chapter IDs naturally
        sorted_chapter_ids = sorted(chapter_groups.keys(), key=natural_chapter_sort_key)

        for chap_id in sorted_chapter_ids:
            chapter_pages = chapter_groups[chap_id]
            # Sort pages numerically by page index
            sorted_pages = sorted(chapter_pages, key=lambda x: x['page'])

            chapter_folder_name = format_chapter_folder_name(chap_id)
            chapter_dir = os.path.join(series_dir, chapter_folder_name)
            os.makedirs(chapter_dir, exist_ok=True)

            print(f"  Writing {chapter_folder_name} ({len(sorted_pages)} pages)...")

            for i, p in enumerate(sorted_pages, start=1):
                dest_file_name = f"image_{i}.webp"
                dest_path = os.path.join(chapter_dir, dest_file_name)

                with zipfile.ZipFile(p['archive'], 'r') as z:
                    # Write the webp file directly without transcoding
                    data = z.read(p['name'])
                    with open(dest_path, 'wb') as df:
                        df.write(data)

    print("\nProcessing complete!")

def main() -> None:
    parser = argparse.ArgumentParser(description="Parse CBR books into organized chapters.")
    parser.add_argument("--source", default="./source", help="Source directory containing .cbr files")
    parser.add_argument("--output", default="./output", help="Output directory to place parsed structure")
    args = parser.parse_args()

    process_books(args.source, args.output)

if __name__ == "__main__":
    main()
