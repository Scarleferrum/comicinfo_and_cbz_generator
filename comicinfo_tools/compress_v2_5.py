import argparse
import json
import os
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(_PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(_PROJECT_DIR))

from comicinfo_core.files_v2_5 import zip_folder as _zip_folder
from comicinfo_core.pipeline_v2_5 import run_batch_compress

BASE_DIR = _PROJECT_DIR


def zip_folder(folder_path, zip_path):
    try:
        _zip_folder(folder_path, zip_path, exclude_system_files=True)
        return {"status": "success", "folder": os.path.basename(folder_path)}
    except Exception as e:
        return {"status": "error", "folder": folder_path, "error": str(e)}


def zip_folder_gui(folder, output_dir):
    zip_path = Path(output_dir) / (Path(folder).name + ".zip")
    return str(_zip_folder(folder, zip_path, exclude_system_files=False))


def run_compress(
    input_dir=None,
    workers=None,
    force=False,
    debug=False,
    cpu_core_limit=None,
    memory_limit_percent=40,
):
    if not input_dir:
        input_dir = BASE_DIR / "模式二輸出"
    else:
        input_dir = Path(input_dir)

    input_dir = input_dir.resolve()

    if debug:
        print(f"[DEBUG] input_dir = {input_dir}")

    if workers is None:
        workers = os.cpu_count() or 4

    return run_batch_compress(
        input_dir,
        force=force,
        workers=workers,
        cpu_core_limit=cpu_core_limit,
        memory_limit_percent=memory_limit_percent,
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Compress subfolders into zip files")

    parser.add_argument("--input", default="output")
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--output-format", choices=["text", "json"], default="text")
    parser.add_argument("--gui", action="store_true")

    return parser.parse_args()


def output_result(result, fmt):
    if fmt == "json":
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"[{result['status'].upper()}]")
        if "data" in result:
            print(result["data"])


def run(context=None):
    """GUI and pipeline entry point."""
    input_dir = None

    if context:
        input_dir = context.get("output_dir") or context.get("input_dir")

    # The GUI treats batch generation as an iterative update workflow.
    force = bool(context and context.get("force", True))
    workers = None
    cpu_core_limit = None
    memory_limit_percent = 40
    if context:
        configured_threads = int(context.get("max_compression_threads", 2))
        configured_cores = int(context.get("cpu_core_limit", 2))
        workers = min(configured_threads, configured_cores)
        cpu_core_limit = configured_cores
        memory_limit_percent = int(context.get("memory_limit_percent", 40))
    return run_compress(
        input_dir=input_dir,
        workers=workers,
        force=force,
        cpu_core_limit=cpu_core_limit,
        memory_limit_percent=memory_limit_percent,
    )


def main():
    args = parse_args()

    result = run_compress(
        input_dir=args.input,
        workers=args.workers,
        force=args.force,
    )

    if args.gui:
        # This optional result window is only used by the CLI entry point.
        import tkinter as tk

        root = tk.Tk()
        root.title("Compress Result")

        text = tk.Text(root)
        text.pack(expand=True, fill="both")
        text.insert("1.0", json.dumps(result, indent=2, ensure_ascii=False))
        text.config(state="disabled")

        root.mainloop()
    else:
        output_result(result, args.output_format)

    return result


if __name__ == "__main__":
    main()
