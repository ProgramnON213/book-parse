import os
import re
import json
import zipfile
import argparse
import shutil
import datetime
from functools import lru_cache
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
from collections import defaultdict
from PIL import Image

try:
    import rarfile
    HAS_RARFILE = True
except ImportError:
    rarfile = None
    HAS_RARFILE = False

@dataclass
class PageInfo:
    name: str
    chapter: str
    page: int
    is_cover: bool

@dataclass
class ArchiveEntry:
    filename: str
    file_size: int
    _is_dir: bool

    def is_dir(self) -> bool:
        return self._is_dir

class ArchiveReader:
    """
    Unified context manager wrapper for zipfile.ZipFile, rarfile.RarFile archives, and uncompressed book directories.
    """
    def __init__(self, archive_path: str):
        self.archive_path = archive_path
        self.archive_type = None
        self.archive_obj = None

    @classmethod
    def is_archive(cls, path: str) -> bool:
        if zipfile.is_zipfile(path):
            return True
        if HAS_RARFILE and rarfile and rarfile.is_rarfile(path):
            return True
        if os.path.isdir(path):
            return True
        return False

    def __enter__(self):
        if zipfile.is_zipfile(self.archive_path):
            self.archive_type = 'zip'
            self.archive_obj = zipfile.ZipFile(self.archive_path, 'r')
            return self
        elif HAS_RARFILE and rarfile and rarfile.is_rarfile(self.archive_path):
            self.archive_type = 'rar'
            self.archive_obj = rarfile.RarFile(self.archive_path, 'r')
            return self
        elif os.path.isdir(self.archive_path):
            self.archive_type = 'dir'
            return self
        elif self.archive_path.lower().endswith('.rar') and not HAS_RARFILE:
            raise ImportError("Processing '.rar' archives requires the 'rarfile' Python package. Please install it with 'pip install rarfile'.")
        else:
            raise ValueError(f"'{os.path.basename(self.archive_path)}' is not a valid zip/rar archive or directory.")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.archive_obj:
            self.archive_obj.close()

    def infolist(self) -> List[ArchiveEntry]:
        if self.archive_type == 'dir':
            entries = []
            for root, dirs, files in os.walk(self.archive_path):
                for f in files:
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, self.archive_path).replace('\\', '/')
                    entries.append(ArchiveEntry(rel_p, os.path.getsize(full_p), False))
                for d in dirs:
                    full_p = os.path.join(root, d)
                    rel_p = os.path.relpath(full_p, self.archive_path).replace('\\', '/')
                    entries.append(ArchiveEntry(rel_p, 0, True))
            return entries
        return [
            ArchiveEntry(
                info.filename,
                info.file_size,
                info.is_dir() if self.archive_type == 'zip' else (info.isdir() if hasattr(info, 'isdir') else info.is_dir())
            )
            for info in self.archive_obj.infolist()
        ]

    def read(self, name: str) -> bytes:
        if self.archive_type == 'dir':
            file_path = _safe_join(self.archive_path, name)
            with open(file_path, 'rb') as f:
                return f.read()
        return self.archive_obj.read(name)

    def open(self, name: str):
        if self.archive_type == 'dir':
            file_path = _safe_join(self.archive_path, name)
            return open(file_path, 'rb')
        return self.archive_obj.open(name)


# Pre-compiled regular expressions for parsing chapter IDs and page info
CHAPTER_PATTERN_PREFER = re.compile(r' - (c\d+(?:x\d+)?)\b')
CHAPTER_PATTERN_FALLBACK = re.compile(r'\b(c\d+(?:x\d+)?)\b')
PAGE_PATTERN_PREFER = re.compile(r' - p(\d+)')
PAGE_PATTERN_FALLBACK = re.compile(r'\bp(\d+)')
NATURAL_SORT_PATTERN = re.compile(r'^c(\d+)(?:x(\d+))?$')

WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
}

def sanitize_folder_name(name: str) -> str:
    """
    Sanitizes a string to make it safe for directory names by replacing invalid characters,
    handling Windows reserved filenames, and replacing trailing dots/spaces.
    """
    sanitized = re.sub(r'[\\/*?:"<>|]', '_', name).strip()
    sanitized = re.sub(r'[\. ]+$', '_', sanitized)
    if not sanitized:
        return "_"
    
    stem, ext = os.path.splitext(sanitized)
    if stem.upper() in WINDOWS_RESERVED_NAMES:
        return f"_{sanitized}_"
    
    return sanitized

def _safe_join(base_dir: str, *paths: str) -> str:
    """
    Safely joins paths onto base_dir and verifies the result does not escape base_dir.
    Raises ValueError if target path escapes base_dir.
    """
    target = os.path.join(base_dir, *paths)
    abs_base = os.path.realpath(base_dir)
    abs_target = os.path.realpath(target)
    try:
        if os.path.commonpath([abs_base, abs_target]) != abs_base:
            raise ValueError(f"Target path '{target}' escapes base directory '{base_dir}'.")
    except ValueError as e:
        raise ValueError(f"Target path '{target}' escapes base directory '{base_dir}': {e}")
    return target

# Security constraints to prevent Denial of Service (DoS) / Zip Bomb attacks
MAX_FILE_SIZE = 100 * 1024 * 1024  # Max size for individual extracted files (100 MB)
MAX_BOOK_UNCOMPRESSED_SIZE = 1024 * 1024 * 1024  # Max total uncompressed size for a book archive (1 GB)

def check_safe_path(base_dir: str, target_path: str) -> bool:
    """
    Verifies that target_path is strictly inside base_dir to prevent directory traversal.
    Delegates to _safe_join to eliminate duplicate path resolution logic.
    """
    try:
        _safe_join(base_dir, target_path)
        return True
    except ValueError:
        return False

def archive_source_file(source_file_path: str, archive_dir: str, base_dir: str = None) -> str:
    """
    Moves a processed source file into the archive directory.
    If a file with the same name exists in archive_dir, appends a timestamp suffix.
    Optionally checks path safety against base_dir if base_dir is provided.
    Returns the destination file path.
    """
    if base_dir and not check_safe_path(base_dir, archive_dir):
        raise ValueError(f"Archive directory '{archive_dir}' is outside base directory '{base_dir}'.")
    
    os.makedirs(archive_dir, exist_ok=True)
    filename = os.path.basename(source_file_path)
    dest_path = os.path.join(archive_dir, filename)

    if os.path.exists(dest_path):
        name_stem, ext = os.path.splitext(filename)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_path = os.path.join(archive_dir, f"{name_stem}_{timestamp}{ext}")

    shutil.move(source_file_path, dest_path)
    return dest_path

@lru_cache(maxsize=1024)
def extract_chapter_id(filename: str) -> str:
    """
    Extracts chapter identifier (e.g. 'c001', 'c005x1') from a page filename.
    """
    match = CHAPTER_PATTERN_PREFER.search(filename) or CHAPTER_PATTERN_FALLBACK.search(filename)
    return match.group(1) if match else ""

@lru_cache(maxsize=1024)
def extract_page_info(filename: str) -> int:
    """
    Extracts the page starting index (e.g. 'p001' -> 1, 'p174-p175' -> 174, '1.jpg' -> 1) from a page filename.
    """
    match = PAGE_PATTERN_PREFER.search(filename) or PAGE_PATTERN_FALLBACK.search(filename)
    if match:
        return int(match.group(1))
    
    stem = os.path.splitext(os.path.basename(filename))[0]
    match = re.search(r'(\d+)', stem)
    return int(match.group(1)) if match else 0

@lru_cache(maxsize=1024)
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

@lru_cache(maxsize=1024)
def format_chapter_folder_name(chapter_id: str) -> str:
    """
    Formats the chapter folder name based on the chapter ID.
    e.g. 'c001' -> 'chapter_1', 'c005x1' -> 'chapter_5_extra_1'.
    """
    chapter_num, extra_num = natural_chapter_sort_key(chapter_id)
    if extra_num > 0:
        return f"chapter_{chapter_num}_extra_{extra_num}"
    if chapter_num != 9999:
        return f"chapter_{chapter_num}"
    return sanitize_folder_name(chapter_id)

def load_toc_data(archive_path: str, z: ArchiveReader) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Attempts to locate and parse 'toc.json' from inside the archive or alongside archive_path.
    Enforces security size limits (MAX_FILE_SIZE) and filters out hidden/system paths.
    Returns a tuple of (parsed_json_dict_or_None, raw_json_str_or_empty).
    """
    # 1. Search inside archive
    for info in z.infolist():
        parts = info.filename.replace('\\', '/').split('/')
        is_system_path = any(p.startswith('.') or p.startswith('__MACOSX') for p in parts if p)
        base = os.path.basename(info.filename)
        if base.lower() == "toc.json" and not is_system_path:
            if info.file_size > MAX_FILE_SIZE:
                print(f"Warning: 'toc.json' inside archive exceeds size limit ({info.file_size} B). Skipping.")
                return None, ""
            try:
                raw_bytes = z.read(info.filename)
                raw_str = raw_bytes.decode('utf-8-sig', errors='replace')
                data = json.loads(raw_str)
                if isinstance(data, dict) and "chapters" in data and isinstance(data["chapters"], list):
                    return data, raw_str
            except Exception as e:
                if HAS_RARFILE and rarfile and hasattr(rarfile, 'RarCannotExec') and isinstance(e, rarfile.RarCannotExec):
                    raise e
                print(f"Warning: Found 'toc.json' inside archive but failed to parse: {e}")
                return None, ""


    # 2. Search alongside archive file in source directory
    stem = os.path.splitext(archive_path)[0]
    dir_name = os.path.dirname(archive_path)
    candidates = [
        f"{stem}.toc.json",
        os.path.join(dir_name, "toc.json"),
    ]
    for cand in candidates:
        if os.path.isfile(cand):
            file_size = os.path.getsize(cand)
            if file_size > MAX_FILE_SIZE:
                print(f"Warning: External TOC file '{cand}' exceeds size limit ({file_size} B). Skipping.")
                continue
            try:
                with open(cand, 'r', encoding='utf-8-sig') as f:
                    raw_str = f.read()
                    data = json.loads(raw_str)
                    if isinstance(data, dict) and "chapters" in data and isinstance(data["chapters"], list):
                        return data, raw_str
            except Exception as e:
                print(f"Warning: Found external TOC file '{cand}' but failed to parse: {e}")

    return None, ""

def load_meta_data(archive_path: str, z: ArchiveReader) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Attempts to locate and parse 'meta.json' from inside the archive or alongside archive_path.
    Enforces security size limits (MAX_FILE_SIZE) and filters out hidden/system paths.
    Returns a tuple of (parsed_json_dict_or_None, raw_json_str_or_empty).
    """
    # 1. Search inside archive
    for info in z.infolist():
        parts = info.filename.replace('\\', '/').split('/')
        is_system_path = any(p.startswith('.') or p.startswith('__MACOSX') for p in parts if p)
        base = os.path.basename(info.filename)
        if base.lower() == "meta.json" and not is_system_path:
            if info.file_size > MAX_FILE_SIZE:
                print(f"Warning: 'meta.json' inside archive exceeds size limit ({info.file_size} B). Skipping.")
                return None, ""
            try:
                raw_bytes = z.read(info.filename)
                raw_str = raw_bytes.decode('utf-8-sig', errors='replace')
                data = json.loads(raw_str)
                if isinstance(data, dict):
                    return data, raw_str
            except Exception as e:
                if HAS_RARFILE and rarfile and hasattr(rarfile, 'RarCannotExec') and isinstance(e, rarfile.RarCannotExec):
                    raise e
                print(f"Warning: Found 'meta.json' inside archive but failed to parse: {e}")
                return None, ""

    # 2. Search alongside archive file in source directory
    stem = os.path.splitext(archive_path)[0]
    dir_name = os.path.dirname(archive_path)
    candidates = [
        f"{stem}.meta.json",
        os.path.join(dir_name, "meta.json"),
    ]
    for cand in candidates:
        if os.path.isfile(cand):
            file_size = os.path.getsize(cand)
            if file_size > MAX_FILE_SIZE:
                print(f"Warning: External meta file '{cand}' exceeds size limit ({file_size} B). Skipping.")
                continue
            try:
                with open(cand, 'r', encoding='utf-8-sig') as f:
                    raw_str = f.read()
                    data = json.loads(raw_str)
                    if isinstance(data, dict):
                        return data, raw_str
            except Exception as e:
                print(f"Warning: Found external meta file '{cand}' but failed to parse: {e}")

    return None, ""

STATUS_VALUES_DEFAULT = [
    "0 = Unknown",
    "1 = Ongoing",
    "2 = Completed",
    "3 = Licensed",
    "4 = Publishing finished",
    "5 = Cancelled",
    "6 = On hiatus"
]

def transform_meta_to_details(meta_data: Dict[str, Any], meta_engine: str = "n20") -> Dict[str, Any]:
    """
    Transforms raw meta.json data dictionary into details.json dictionary.
    Supports engine mode (default 'n20').
    """
    raw_title = meta_data.get("title")
    title_str = ""
    if isinstance(raw_title, dict):
        if "english" in raw_title and raw_title["english"]:
            title_str = str(raw_title["english"])
        else:
            for v in raw_title.values():
                if v:
                    title_str = str(v)
                    break
    elif isinstance(raw_title, str):
        title_str = raw_title
    elif raw_title is not None:
        title_str = str(raw_title)

    tags_list = meta_data.get("tags") if isinstance(meta_data.get("tags"), list) else []

    artist_names = []
    author_names = []
    genre_names = []

    for tag in tags_list:
        if isinstance(tag, dict):
            tag_type = tag.get("type", "")
            tag_name = tag.get("name", "")
            if not tag_name:
                continue
            if tag_type == "artist":
                artist_names.append(tag_name)
            elif tag_type in ("group", "author"):
                author_names.append(tag_name)
            elif tag_type == "tag":
                genre_names.append(tag_name)
        elif isinstance(tag, str):
            genre_names.append(tag)

    artist_str = ", ".join(artist_names) if artist_names else str(meta_data.get("artist", ""))
    author_str = ", ".join(author_names) if author_names else str(meta_data.get("author", ""))

    return {
        "title": title_str,
        "author": author_str,
        "artist": artist_str,
        "description": "none",
        "genre": genre_names,
        "status": "2",
        "_status values": STATUS_VALUES_DEFAULT
    }

def group_pages_by_toc(pages: List[PageInfo], toc_data: Dict[str, Any]) -> Dict[str, List[PageInfo]]:
    """
    Groups page information by Table of Contents chapter definitions using start_page and end_page ranges.
    Non-cXXXX chapter IDs (e.g. 'finale', 'appendix') are assigned sequential chapter IDs (c001, c002...).
    Leading pages before Chapter 1 are routed to c000 (chapter_0).
    Pages outside explicit TOC ranges are isolated into extra folders (c{N}x1 -> chapter_N_extra_1).
    """
    sorted_all_pages = sorted(pages, key=lambda x: (natural_chapter_sort_key(x.chapter or "c001"), x.page, x.name))
    raw_chapters = toc_data.get("chapters", [])

    if not raw_chapters:
        chapter_groups = defaultdict(list)
        chapter_groups["c001"].extend(sorted_all_pages)
        return chapter_groups

    resolved_chapters = []
    current_chap_num = 0

    for chap in raw_chapters:
        raw_id = chap.get("id") or ""
        chap_num, extra_num = natural_chapter_sort_key(raw_id)
        if chap_num != 9999:
            current_chap_num = max(current_chap_num, chap_num)
            res_id = raw_id
        else:
            current_chap_num += 1
            res_id = f"c{current_chap_num:03d}"

        c_copy = dict(chap)
        c_copy["resolved_id"] = res_id
        resolved_chapters.append(c_copy)

    first_start = resolved_chapters[0].get("start_page", 1)
    last_end = resolved_chapters[-1].get("end_page")
    last_chap_id = resolved_chapters[-1]["resolved_id"]

    chap_num, extra_num = natural_chapter_sort_key(last_chap_id)
    trailing_extra_id = f"c{chap_num:03d}x{extra_num + 1}" if chap_num != 9999 else f"{last_chap_id}_extra_1"

    chapter_groups = defaultdict(list)

    for i, page_obj in enumerate(sorted_all_pages, start=1):
        if i < first_start:
            # Leading pages before Chapter 1 -> chapter_0
            chapter_groups["c000"].append(page_obj)
        elif last_end is not None and i > last_end:
            # Trailing pages past last chapter -> chapter_N_extra_1
            chapter_groups[trailing_extra_id].append(page_obj)
        else:
            # Check if page falls strictly inside any defined chapter range
            assigned_id = None
            prev_chap_id = resolved_chapters[0]["resolved_id"]
            for chap in resolved_chapters:
                s_p = chap.get("start_page", 1)
                if s_p <= i:
                    prev_chap_id = chap["resolved_id"]
                e_p = chap.get("end_page")
                if s_p <= i and (e_p is None or i <= e_p):
                    assigned_id = chap["resolved_id"]
                    break

            if assigned_id is None:
                # Gap between chapters: isolate into extra folder of preceding chapter
                p_num, p_extra = natural_chapter_sort_key(prev_chap_id)
                assigned_id = f"c{p_num:03d}x{p_extra + 1}" if p_num != 9999 else f"{prev_chap_id}_extra_1"

            chapter_groups[assigned_id].append(page_obj)

    return chapter_groups


def _save_cover_image(z: ArchiveReader, cover_page_name: str, book_dir: str) -> None:
    """
    Extracts and converts the cover image to cover.jpg inside book_dir.
    Handles color mode conversions and transparency safely.
    """
    cover_path = _safe_join(book_dir, "cover.jpg")
    with z.open(cover_page_name) as zf, Image.open(zf) as img:
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            rgb_img = background
        else:
            rgb_img = img.convert('RGB')
        rgb_img.save(cover_path, "JPEG")

def _extract_and_write_pages(z: ArchiveReader, book_dir: str, chapter_groups: Dict[str, List[PageInfo]]) -> None:
    """
    Extracts chapter image files into output chapter directories using 1 MB stream buffers.
    """
    BUFFER_SIZE = 1024 * 1024  # 1 MB stream buffer for high-performance I/O
    sorted_chapter_ids = sorted(chapter_groups.keys(), key=natural_chapter_sort_key)

    for chap_id in sorted_chapter_ids:
        sorted_pages = sorted(chapter_groups[chap_id], key=lambda x: (x.page, x.name))
        chapter_folder_name = format_chapter_folder_name(chap_id)
        chapter_dir = _safe_join(book_dir, chapter_folder_name)
        os.makedirs(chapter_dir, exist_ok=True)

        print(f"  Writing {chapter_folder_name} ({len(sorted_pages)} pages)...")
        for i, p in enumerate(sorted_pages, start=1):
            ext = os.path.splitext(p.name)[1].lower()
            dest_path = _safe_join(chapter_dir, f"image_{i}{ext}")
            with z.open(p.name) as source, open(dest_path, 'wb') as target:
                shutil.copyfileobj(source, target, length=BUFFER_SIZE)

def process_single_book(archive_path: str, output_dir: str, meta_engine: str = "n20") -> bool:
    """
    Processes a single CBR/CBZ/ZIP/RAR book archive. Returns True if successfully parsed, False otherwise.
    """
    file_name = os.path.basename(archive_path)
    book_folder_name = sanitize_folder_name(os.path.splitext(file_name)[0])

    try:
        if not ArchiveReader.is_archive(archive_path):
            if archive_path.lower().endswith('.rar') and not HAS_RARFILE:
                print(f"Warning: '{file_name}' requires the 'rarfile' package. Please install it with 'pip install rarfile'. Skipping.")
                return False
            print(f"Warning: '{file_name}' is not a valid zip or rar archive (CBR/CBZ/ZIP/RAR). Skipping.")
            return False

        book_dir = _safe_join(output_dir, "local", book_folder_name)

        pages: List[PageInfo] = []
        with ArchiveReader(archive_path) as z:
            total_uncompressed_size = 0
            for info in z.infolist():
                if info.file_size > MAX_FILE_SIZE:
                    raise ValueError(f"Archive member '{info.filename}' size ({info.file_size} B) exceeds maximum allowed size ({MAX_FILE_SIZE} B).")
                total_uncompressed_size += info.file_size
                
                base_name = os.path.basename(info.filename)
                if not info.is_dir() and not base_name.startswith('.') and not base_name.startswith('__MACOSX') and info.filename.lower().endswith(('.webp', '.jpg', '.jpeg', '.png')):
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
                return False

            os.makedirs(book_dir, exist_ok=True)
            print(f"Output directory: {book_dir}")

            # 1. Handle Cover Page
            cover_page = next((p for p in pages if p.is_cover), None)
            if cover_page is None:
                sorted_all_pages = sorted(pages, key=lambda x: (natural_chapter_sort_key(x.chapter or "c001"), x.page, x.name))
                cover_page = sorted_all_pages[0]

            print(f"Generating cover from: {os.path.basename(cover_page.name)}")
            try:
                _save_cover_image(z, cover_page.name, book_dir)
            except Exception as e:
                print(f"Error converting cover image: {e}")

            # 2. Check for Table of Contents (toc.json) and group pages by chapter
            toc_data, raw_toc_str = load_toc_data(archive_path, z)
            if toc_data:
                print("Found valid Table of Contents (toc.json). Using TOC page ranges for chapter grouping.")
                chapter_groups = group_pages_by_toc(pages, toc_data)
            else:
                chapter_groups = defaultdict(list)
                for p in pages:
                    chap_id = p.chapter or "c001"
                    chapter_groups[chap_id].append(p)

            if raw_toc_str:
                try:
                    toc_out_path = _safe_join(book_dir, "toc.json")
                    with open(toc_out_path, "w", encoding="utf-8") as f:
                        f.write(raw_toc_str)
                except Exception as e:
                    print(f"Warning: Failed to write output toc.json: {e}")

            # 3. Check for Metadata (meta.json) and generate details.json
            meta_data, raw_meta_str = load_meta_data(archive_path, z)
            if meta_data:
                try:
                    details_dict = transform_meta_to_details(meta_data, meta_engine)
                    details_out_path = _safe_join(book_dir, "details.json")
                    with open(details_out_path, "w", encoding="utf-8") as f:
                        json.dump(details_dict, f, ensure_ascii=False, indent=2)
                    print(f"Generated details.json from meta.json (engine: {meta_engine})")
                except Exception as e:
                    print(f"Warning: Failed to write output details.json: {e}")

            # 4. Extract & write chapter image files
            _extract_and_write_pages(z, book_dir, chapter_groups)

        return True
    except zipfile.BadZipFile as e:
        print(f"Error: '{file_name}' is a corrupted zip archive: {e}. Skipping.")
        return False
    except Exception as e:
        if HAS_RARFILE and rarfile:
            if hasattr(rarfile, 'RarCannotExec') and isinstance(e, rarfile.RarCannotExec):
                print(f"Warning: '{file_name}' requires an unrar CLI tool (e.g. 'unrar', 'bsdtar', or '7z') on your system PATH: {e}. Skipping.")
                return False
            if isinstance(e, rarfile.Error):
                print(f"Error: '{file_name}' is a corrupted rar archive: {e}. Skipping.")
                return False
        print(f"Error processing book '{file_name}': {e}. Skipping.")
        return False


def process_books(source_dir: str, output_dir: str, archive_dir: str = "./archive", meta_engine: str = "n20") -> Dict[str, int]:
    """
    Processes all CBR, CBZ, ZIP, and RAR books and uncompressed book directories in source_dir, organizing them into output_dir.
    Moves successfully parsed files/directories into archive_dir if specified.
    Returns a summary dictionary of execution metrics.
    """
    summary = {
        "total_found": 0,
        "successfully_parsed": 0,
        "archived": 0,
        "failed": 0,
    }

    if not os.path.exists(source_dir):
        print(f"Source directory '{source_dir}' does not exist.")
        return summary

    book_items = []
    for item in sorted(os.listdir(source_dir)):
        full_p = os.path.join(source_dir, item)
        if os.path.isfile(full_p) and item.lower().endswith(('.cbr', '.cbz', '.zip', '.rar')):
            book_items.append(item)
        elif os.path.isdir(full_p) and not item.startswith('.') and item.lower() != '__macosx':
            book_items.append(item)

    if not book_items:
        print(f"No .cbr, .cbz, .zip, .rar files or book directories found in '{source_dir}'.")
        return summary

    summary["total_found"] = len(book_items)
    print(f"Found {len(book_items)} books to process.")

    for file_name in book_items:
        archive_path = os.path.join(source_dir, file_name)
        print(f"\nProcessing book: '{file_name}'")
        success = process_single_book(archive_path, output_dir, meta_engine=meta_engine)
        if success:
            summary["successfully_parsed"] += 1
            if archive_dir:
                archived_file = archive_source_file(archive_path, archive_dir)
                summary["archived"] += 1
                print(f"Archived '{file_name}' -> '{archived_file}'")
        else:
            summary["failed"] += 1


    print("\nProcessing complete!")
    print("=" * 50)
    print("Execution Summary:")
    print(f"  - Total books found:       {summary['total_found']}")
    print(f"  - Successfully parsed:     {summary['successfully_parsed']}")
    print(f"  - Archived:                {summary['archived']}")
    print(f"  - Failed / Skipped:        {summary['failed']}")
    print("=" * 50)

    return summary

def main() -> None:
    parser = argparse.ArgumentParser(description="Parse CBR/CBZ/ZIP/RAR books into organized chapters.")
    parser.add_argument("--source", default="./source", help="Source directory containing .cbr, .cbz, .zip, or .rar files")
    parser.add_argument("--output", default="./output", help="Output directory to place parsed structure")
    parser.add_argument("--archive", default="./archive", help="Archive directory to move processed books (set empty string to disable)")
    parser.add_argument("--meta", default="n20", help="Metadata engine format (default: n20)")
    args = parser.parse_args()

    process_books(args.source, args.output, archive_dir=args.archive, meta_engine=args.meta)


if __name__ == "__main__":
    main()

