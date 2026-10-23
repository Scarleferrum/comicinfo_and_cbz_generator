"""Canonical ComicInfo field definitions shared by the GUI and Excel paths."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Field:
    key: str
    label: str
    default: str = ""
    integer: bool = False


FIELDS = (
    Field("Title", "標題"),
    Field("Series", "系列"),
    Field("Number", "集數", integer=True),
    Field("Count", "總集數", integer=True),
    Field("Summary", "摘要"),
    Field("Year", "年份", integer=True),
    Field("Month", "月份", integer=True),
    Field("Day", "日期", integer=True),
    Field("Writer", "作者"),
    Field("Publisher", "出版社"),
    Field("Genre", "類型"),
    Field("Tags", "標籤"),
    Field("Web", "網站"),
    Field("LanguageISO", "語言", "zh-Hant"),
    Field("Format", "格式", "Digital"),
    Field("BlackAndWhite", "黑白", "No"),
    Field("Manga", "漫畫方向", "YesAndRightToLeft"),
    Field("Characters", "角色"),
    Field("Teams", "團隊"),
    Field("AgeRating", "分級"),
)

EXCEL_HEADERS = tuple(field.key for field in FIELDS)
FIELD_BY_KEY = {field.key: field for field in FIELDS}

XML_FIELDS = EXCEL_HEADERS[:9] + (
    "Penciller", "Inker", "Colorist", "Letterer", "CoverArtist", "Editor",
) + EXCEL_HEADERS[9:13] + ("PageCount",) + EXCEL_HEADERS[13:]
XML_EMPTY_FIELDS = frozenset(
    (
        "Penciller",
        "Inker",
        "Colorist",
        "Letterer",
        "CoverArtist",
        "Editor",
        "PageCount",
    )
)
