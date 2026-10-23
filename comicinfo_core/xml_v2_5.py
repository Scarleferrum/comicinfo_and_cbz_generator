"""ComicInfo XML serialization shared by both creation modes."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from .fields_v2_5 import XML_EMPTY_FIELDS, XML_FIELDS
from .model_v2_5 import ComicMetadata

SCHEMA_URL = "https://raw.githubusercontent.com/anansi-project/comicinfo/main/schema/v2.0/ComicInfo.xsd"


def build_xml(data: ComicMetadata | dict[str, str]) -> ET.Element:
    comic = data if isinstance(data, ComicMetadata) else ComicMetadata(data)
    root = ET.Element(
        "ComicInfo",
        {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation": SCHEMA_URL,
        },
    )
    for name in XML_FIELDS:
        node = ET.SubElement(root, name)
        node.text = "" if name in XML_EMPTY_FIELDS else comic.get(name, "")
    return root


def write_xml(path: str | Path, data: ComicMetadata | dict[str, str]) -> Path:
    path = Path(path)
    root = build_xml(data)
    try:
        ET.indent(root, space="    ")
    except AttributeError:
        pass
    ET.ElementTree(root).write(
        path,
        encoding="utf-8",
        xml_declaration=True,
        short_empty_elements=False,
    )
    return path
