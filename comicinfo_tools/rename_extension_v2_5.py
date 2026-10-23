from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[1]


def rename_extension(file_path: str, old_ext: str, new_ext: str):
    for root, _, files in os.walk(file_path):
        for f in files:
            if f.endswith(old_ext):
                base = f[:-len(old_ext)]
                os.replace(os.path.join(root, f), os.path.join(root, base + new_ext))


# ✅ plugin-safe
def run(context=None):
    context = context or {}
    output_folder = context.get("output_dir") or BASE_DIR / "模式二輸出"
    rename_extension(str(output_folder), ".zip", ".cbz")


def main():
    run()


if __name__ == "__main__":
    main()
