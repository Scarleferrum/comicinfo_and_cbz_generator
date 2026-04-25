from pathlib import Path
import pandas as pd
import xml.etree.ElementTree as ET
from xml.dom import minidom

# =========================
# 專案根目錄
# =========================
BASE_DIR = Path(__file__).resolve().parents[2]

DEFAULT_EXCEL = BASE_DIR / "input_v2.3.xlsx"
DEFAULT_OUTPUT = BASE_DIR / "模式二輸出"


# =========================
# 工具
# =========================
def sanitize_folder_name(name: str) -> str:
    invalid_chars = r'<>:"/\\|?*'
    for c in invalid_chars:
        name = name.replace(c, "_")
    return name.strip()


def add_tag(parent, tag, text):
    elem = ET.SubElement(parent, tag)
    elem.text = "" if pd.isna(text) else str(text)


def add_default(parent, tag, default_value, text):
    elem = ET.SubElement(parent, tag)
    elem.text = default_value if pd.isna(text) else str(text)


def to_int_str(value):
    if pd.isna(value):
        return ""
    try:
        return str(int(float(value)))
    except:
        return str(value)


def prettify(elem):
    rough = ET.tostring(elem, encoding="utf-8")
    reparsed = minidom.parseString(rough)

    for node in reparsed.getElementsByTagName("*"):
        if node.firstChild is None:
            node.appendChild(reparsed.createTextNode(""))

    return reparsed.toprettyxml(indent="    ", encoding="utf-8")


# =========================
# XML Builder
# =========================
def create_xml(row):
    root = ET.Element(
        "ComicInfo",
        {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation":
                "https://raw.githubusercontent.com/anansi-project/comicinfo/main/schema/v2.0/ComicInfo.xsd"
        }
    )

    add_tag(root, "Title", row.get("Title"))
    add_tag(root, "Series", row.get("Series"))
    add_tag(root, "Number", to_int_str(row.get("Number")))
    add_tag(root, "Count", to_int_str(row.get("Count")))
    add_tag(root, "Summary", row.get("Summary"))

    for tag in ["Year", "Month", "Day"]:
        add_tag(root, tag, to_int_str(row.get(tag)))

    add_tag(root, "Writer", row.get("Writer"))

    for tag in ["Penciller", "Inker", "Colorist", "Letterer", "CoverArtist", "Editor"]:
        add_tag(root, tag, "")

    for tag in ["Publisher", "Genre", "Tags", "Web"]:
        add_tag(root, tag, row.get(tag))

    add_tag(root, "PageCount", "")
    add_default(root, "LanguageISO", "zh-Hant", row.get("LanguageISO"))
    add_default(root, "Format", "Digital", row.get("Format"))
    add_default(root, "BlackAndWhite", "No", row.get("BlackAndWhite"))
    add_default(root, "Manga", "YesAndRightToLeft", row.get("Manga"))

    add_tag(root, "Characters", row.get("Characters"))
    add_tag(root, "Teams", row.get("Teams"))
    add_tag(root, "AgeRating", row.get("AgeRating"))

    return root


# =========================
# 核心執行邏輯（抽出）
# =========================
def run_generate(excel_path=None, output_dir=None):
    excel_path = Path(excel_path) if excel_path else DEFAULT_EXCEL
    output_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT

    excel_path = excel_path.resolve()
    output_dir = output_dir.resolve()

    if not excel_path.exists():
        raise FileNotFoundError(f"Excel 不存在: {excel_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(excel_path)

    for idx, row in df.iterrows():
        title = row.get("Title")

        if pd.isna(title):
            print(f"⚠️ 第 {idx+1} 列沒有 Title，跳過")
            continue

        folder_name = sanitize_folder_name(str(title))
        target_dir = output_dir / folder_name
        target_dir.mkdir(parents=True, exist_ok=True)

        xml_root = create_xml(row)
        xml_data = prettify(xml_root)

        output_file = target_dir / "comicinfo.xml"
        output_file.write_bytes(xml_data)

        print(f"✔ 已生成: {output_file}")

    return {
        "status": "success",
        "rows": len(df)
    }


# =========================
# plugin 入口（⭐ 重點）
# =========================
def run(context=None):
    """
    GUI / pipeline 使用
    """
    excel_path = None
    output_dir = None

    if context:
        excel_path = context.get("excel_path")
        output_dir = context.get("output_dir")

    return run_generate(
        excel_path=excel_path,
        output_dir=output_dir
    )


# =========================
# CLI
# =========================
def main():
    return run_generate()


if __name__ == "__main__":
    main()