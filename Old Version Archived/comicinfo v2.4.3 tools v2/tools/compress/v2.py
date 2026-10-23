import os
import zipfile
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# ==================
# 排除規則

EXCLUDE_FILES = {
    ".DS_Store",# MacOS 系統文件
    "Thumbs.db",# Windows 系統文件
    "desktop.ini",# Windows 系統文件
}

EXCLUDE_PREFIX = "._"# MacOS 生成的隱藏文件

# ==================
# 全局常量（根目錄）

BASE_DIR = Path(__file__).resolve().parents[2]

# ==================
# 排除指定文件

def should_exclude(filename):
    return filename in EXCLUDE_FILES or filename.startswith(EXCLUDE_PREFIX)

# ==================
# 壓縮函數

def zip_folder(folder_path, zip_path):
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    if should_exclude(file):
                        continue

                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, folder_path)
                    zipf.write(file_path, arcname)

        return {"status": "success", "folder": os.path.basename(folder_path)}
    except Exception as e:
        return {
            "status": "error",
            "folder": folder_path,
            "error": str(e)
        }

def zip_folder_gui(folder, output_dir):
    folder = os.path.abspath(folder)
    output_dir = os.path.abspath(output_dir)

    zip_path = os.path.join(output_dir, os.path.basename(folder) + ".zip")

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(folder):
            for f in files:
                full = os.path.join(root, f)
                arc = os.path.relpath(full, folder)
                z.write(full, arc)

    return zip_path


# ===== 對外 API =====
def run_compress(input_dir=None, workers=None, force=False, debug=False):
    # ===== 路徑解析（核心修正）=====
    if not input_dir:
        input_dir = BASE_DIR / "模式二輸出"
    else:
        input_dir = Path(input_dir)

    input_dir = input_dir.resolve()

    if debug:
        print(f"[DEBUG] input_dir = {input_dir}")

    if workers is None:
        workers = os.cpu_count() or 4

    result = {
        "status": "success",
        "data": {
            "processed": 0,
            "skipped": 0,
            "errors": 0
        }
    }

    if not os.path.exists(input_dir):
        return {
            "status": "error",
            "message": f"input dir not found: {input_dir}"
        }

    tasks = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        for item in os.listdir(input_dir):
            item_path = os.path.join(input_dir, item)

            if not os.path.isdir(item_path):
                continue

            zip_path = os.path.join(input_dir, f"{item}.zip")

            if os.path.exists(zip_path) and not force:
                result["data"]["skipped"] += 1
                continue

            future = executor.submit(zip_folder, item_path, zip_path)
            tasks.append(future)

        for future in as_completed(tasks):
            r = future.result()
            if r["status"] == "success":
                result["data"]["processed"] += 1
            else:
                result["data"]["errors"] += 1

    if result["data"]["errors"] > 0:
        result["status"] = "partial"

    return result


# ===== CLI =====
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


# ===== plugin-safe entry（關鍵修正）=====
def run(context=None):
    """
    GUI / pipeline 專用入口
    """
    input_dir = None

    if context:
        # ⭐ 兼容你的主程式
        input_dir = context.get("output_dir") or context.get("input_dir")

    return run_compress(input_dir=input_dir)


# ===== main（CLI only）=====
def main():
    
    args = parse_args()

    result = run_compress(
        input_dir=args.input,
        workers=args.workers,
        force=args.force
    )

    if args.gui:
        # ⚠️ CLI 才允許 GUI
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