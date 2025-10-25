import os
import glob
from typing import List, Tuple

TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".rst",
    ".html",
    ".htm",
    ".csv",
    ".json",
    ".yaml",
    ".yml",
    ".xml",
}

DOCX_EXTENSIONS = {
    ".docx",
    ".doc",
}


def is_text_file(path: str) -> bool:
    _, ext = os.path.splitext(path)
    # Support both text and docx files
    if ext.lower() in TEXT_EXTENSIONS or ext.lower() in DOCX_EXTENSIONS:
        return True
    try:
        with open(path, "rb") as f:
            chunk = f.read(2048)
        if b"\x00" in chunk:
            return False
        # Heuristic: treat as text if decodable
        chunk.decode("utf-8", errors="strict")
        return True
    except Exception:
        return False


def read_docx_file(path: str) -> str:
    """Read .docx file and extract text content"""
    try:
        from docx import Document
        doc = Document(path)
        paragraphs = [para.text for para in doc.paragraphs]
        return "\n".join(paragraphs)
    except Exception as e:
        raise RuntimeError(f"Failed to read .docx file: {e}")


def read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def collect_files(input_dir: str | None, patterns: List[str]) -> List[str]:
    files: List[str] = []
    if input_dir:
        # Collect all files under directory
        for root, _, filenames in os.walk(input_dir):
            for name in filenames:
                files.append(os.path.join(root, name))
    for pat in patterns:
        matched = glob.glob(pat)
        files.extend(matched)
    # Deduplicate while preserving order
    seen = set()
    unique_files = []
    for p in files:
        ap = os.path.abspath(p)
        if ap not in seen and os.path.isfile(ap):
            seen.add(ap)
            unique_files.append(ap)
    return unique_files


def load_attachments(input_dir: str | None, paths: List[str]) -> List[Tuple[str, str]]:
    attachments: List[Tuple[str, str]] = []
    files = collect_files(input_dir, paths)
    for path in files:
        if not is_text_file(path):
            continue
        try:
            _, ext = os.path.splitext(path)
            # Read .docx files differently
            if ext.lower() in DOCX_EXTENSIONS:
                content = read_docx_file(path)
            else:
                content = read_text_file(path)
            attachments.append((path, content))
        except Exception:
            # Skip unreadable files
            continue
    return attachments


def chunk_text(text: str, max_chars: int = 8000) -> List[str]:
    if len(text) <= max_chars:
        return [text]
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        # try to break on paragraph boundary
        cut = text.rfind("\n\n", start, end)
        if cut == -1 or cut <= start + int(max_chars * 0.6):
            cut = end
        chunks.append(text[start:cut].strip())
        start = cut
    return [c for c in chunks if c]

