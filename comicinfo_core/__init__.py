"""Reusable services for building ComicInfo metadata and CBZ archives."""

from .excel_v2_5 import append_comic, read_comics
from .files_v2_5 import build_cbz
from .model_v2_5 import ComicMetadata
from .pipeline_v2_5 import generate_batch_xml, generate_single_cbz, run_batch_compress
from .xml_v2_5 import build_xml, write_xml

__all__ = [
    "ComicMetadata",
    "append_comic",
    "build_cbz",
    "build_xml",
    "generate_batch_xml",
    "generate_single_cbz",
    "read_comics",
    "run_batch_compress",
    "write_xml",
]
