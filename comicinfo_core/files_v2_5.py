"""Filesystem and archive operations used by the single and batch workflows."""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".webp")
EXCLUDE_FILES = {".DS_Store", "Thumbs.db", "desktop.ini"}


def collect_images(src_dir: str | Path) -> list[Path]:
    root = Path(src_dir)
    images = [
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ]
    return sorted(images, key=lambda path: str(path).casefold())


def extract_input(src_path: str | Path, temp_dir: str | Path | None = None) -> Path:
    source = Path(src_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"來源不存在: {source}")
    created_temp = temp_dir is None
    destination = (
        Path(tempfile.mkdtemp(prefix="comicinfo_extract_"))
        if created_temp
        else Path(temp_dir)
    )
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(f"暫存資料夾必須不存在或為空: {destination}")
    destination.mkdir(parents=True, exist_ok=True)

    try:
        if source.is_file() and zipfile.is_zipfile(source):
            with zipfile.ZipFile(source) as archive:
                root = destination.resolve()
                for member in archive.infolist():
                    target = (destination / member.filename).resolve()
                    if target != root and root not in target.parents:
                        raise ValueError(f"ZIP 包含不安全路徑: {member.filename}")
                archive.extractall(destination)
        elif source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            raise ValueError("來源必須是 ZIP 檔或資料夾")
    except Exception:
        if created_temp:
            shutil.rmtree(destination, ignore_errors=True)
        raise
    return destination


def zip_folder(
    folder: str | Path,
    zip_path: str | Path,
    exclude_system_files: bool = True,
) -> Path:
    folder = Path(folder)
    zip_path = Path(zip_path)
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(folder.rglob("*")):
            if not path.is_file():
                continue
            excluded = path.name in EXCLUDE_FILES or path.name.startswith("._")
            if exclude_system_files and excluded:
                continue
            archive.write(path, path.relative_to(folder).as_posix())
    return zip_path


def build_cbz(
    files: list[str | Path],
    metadata_xml: str | Path,
    destination: str | Path,
) -> Path:
    """Create a CBZ with the selected images and ComicInfo at the archive root."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        ordered_files = sorted(
            (Path(path) for path in files),
            key=lambda path: path.name.casefold(),
        )
        for item in ordered_files:
            archive.write(item, item.name)
        archive.write(metadata_xml, "comicinfo.xml")
    return destination
