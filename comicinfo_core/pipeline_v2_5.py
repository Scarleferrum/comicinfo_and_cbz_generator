"""Callable single-item and Excel batch pipelines."""

from __future__ import annotations

import os
import re
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from .excel_v2_5 import read_comics_with_rows
from .files_v2_5 import collect_images, extract_input, zip_folder
from .model_v2_5 import ComicMetadata
from .resources_v2_5 import get_hardware_capacity, limit_compression_workers
from .xml_v2_5 import write_xml


def sanitize_name(name: str, replacement: str = "") -> str:
    invalid_characters = r'[<>:"/\\|?*\x00-\x1f]'
    return re.sub(invalid_characters, replacement, str(name)).strip().rstrip(".")


def generate_single_cbz(
    source: str | Path,
    metadata: ComicMetadata | dict[str, Any],
    output_dir: str | Path,
) -> Path:
    comic = metadata if isinstance(metadata, ComicMetadata) else ComicMetadata(metadata)
    title = sanitize_name(comic.get("Title"))
    if not title:
        raise ValueError("Title 不可為空")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    temp = extract_input(source)
    try:
        images = collect_images(temp)
        if not images:
            raise ValueError("來源中找不到支援的圖片")

        # Rebuild a staging folder so re-running a title replaces stale pages as well.
        with tempfile.TemporaryDirectory(
            prefix="comicinfo_build_",
            dir=output_dir,
        ) as staging_root:
            staging = Path(staging_root) / title
            staging.mkdir()
            for image in images:
                shutil.copy2(image, staging / image.name)
            write_xml(staging / "comicinfo.xml", comic)
            archive = zip_folder(staging, output_dir / f"{title}.cbz")
            # Keep the folder output used by existing workflows alongside the CBZ.
            target = output_dir / title
            if target.exists():
                shutil.rmtree(target)
            staging.replace(target)
        return archive
    finally:
        shutil.rmtree(temp, ignore_errors=True)


def generate_batch_xml(
    excel_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    comics_with_rows = read_comics_with_rows(excel_path)
    output_names: dict[str, list[tuple[int, str, str]]] = {}
    for row_number, comic in comics_with_rows:
        title = sanitize_name(comic.get("Title"), "_")
        if not title:
            continue
        output_names.setdefault(title.casefold(), []).append(
            (row_number, title, comic.get("Title"))
        )

    duplicates = [entries for entries in output_names.values() if len(entries) > 1]
    if duplicates:
        details = []
        for entries in duplicates:
            output_name = entries[0][1]
            source_titles = "、".join(
                f"第 {row_number} 列「{source_title}」"
                for row_number, _, source_title in entries
            )
            details.append(f"輸出名稱「{output_name}」：{source_titles}")
        raise ValueError(
            "Excel 標題欄有重複項目或會產生相同資料夾名稱，"
            "已取消整批輸出以避免覆寫：\n- " + "\n- ".join(details)
        )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for _, comic in comics_with_rows:
        title = sanitize_name(comic.get("Title"), "_")
        if not title:
            continue
        folder = output_dir / title
        folder.mkdir(parents=True, exist_ok=True)
        write_xml(folder / "comicinfo.xml", comic)
    return {"status": "success", "rows": len(comics_with_rows)}


def run_batch_compress(
    output_dir: str | Path,
    force: bool = False,
    workers: int | None = None,
    cpu_core_limit: int | None = None,
    memory_limit_percent: int = 40,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    if not output_dir.is_dir():
        raise FileNotFoundError(f"輸出資料夾不存在: {output_dir}")
    processed = skipped = errors = 0
    details = []
    pending_folders = []
    for folder in sorted(output_dir.iterdir()):
        if not folder.is_dir():
            continue
        target = output_dir / f"{folder.name}.zip"
        if target.exists() and not force:
            skipped += 1
        else:
            pending_folders.append((folder, target))

    if not pending_folders:
        return {
            "status": "success",
            "data": {"processed": 0, "skipped": skipped, "errors": 0},
            "details": [],
        }

    if memory_limit_percent not in range(10, 101, 10):
        raise ValueError("memory_limit_percent 必須為 10 至 100，並以 10 為級距")

    if workers is None:
        workers = os.cpu_count() or 4
    capacity = get_hardware_capacity()
    workers = max(1, min(int(workers), capacity.logical_cpus))
    if cpu_core_limit is not None:
        cpu_core_limit = min(
            max(1, int(cpu_core_limit)),
            capacity.physical_cpus,
        )
        workers = min(workers, cpu_core_limit)
    workers = limit_compression_workers(workers, memory_limit_percent)
    if workers < 1:
        raise MemoryError(
            "目前程式或系統可用記憶體低於設定預算，暫停壓縮；"
            "請提高記憶體百分比或關閉其他工作後重試。"
        )
    tasks = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for folder, target in pending_folders:
            tasks.append((folder, executor.submit(zip_folder, folder, target)))
        for folder, future in tasks:
            try:
                future.result()
                processed += 1
            except Exception as exc:
                errors += 1
                details.append({"folder": str(folder), "error": str(exc)})
    return {
        "status": "partial" if errors else "success",
        "data": {
            "processed": processed,
            "skipped": skipped,
            "errors": errors,
        },
        "details": details,
    }
