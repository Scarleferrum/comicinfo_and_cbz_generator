"""Compatibility entry point for the shared batch XML service."""

from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from comicinfo_core.model_v2_5 import ComicMetadata
from comicinfo_core.pipeline_v2_5 import generate_batch_xml
from comicinfo_core.xml_v2_5 import build_xml

DEFAULT_EXCEL = BASE_DIR / "input_v2.4.xlsx"
DEFAULT_OUTPUT = BASE_DIR / "模式二輸出"


def sanitize_folder_name(name: str) -> str:
    from comicinfo_core.pipeline_v2_5 import sanitize_name
    return sanitize_name(name, "_")


def create_xml(row):
    return build_xml(ComicMetadata(dict(row)))


def run_generate(excel_path=None, output_dir=None):
    return generate_batch_xml(excel_path or DEFAULT_EXCEL, output_dir or DEFAULT_OUTPUT)


def run(context=None):
    context = context or {}
    return run_generate(context.get("excel_path"), context.get("output_dir"))


def main():
    return run_generate()


if __name__ == "__main__":
    main()
