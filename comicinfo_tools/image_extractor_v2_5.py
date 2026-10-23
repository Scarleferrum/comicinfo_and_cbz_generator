from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from comicinfo_core.files_v2_5 import collect_images as _collect_images
from comicinfo_core.files_v2_5 import extract_input as _extract_input


def extract_input(src_path, temp_dir=None):
    """Extract a ZIP or copy a directory into a safe temporary location."""
    return str(_extract_input(src_path, temp_dir))


def collect_images(src_dir):
    """
    收集圖片檔案（排序後）
    """
    return [str(path) for path in _collect_images(src_dir)]
