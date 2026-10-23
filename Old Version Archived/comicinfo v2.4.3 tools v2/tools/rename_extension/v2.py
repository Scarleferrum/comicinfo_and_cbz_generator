from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[2]


def change_file_extension(folder_path: Path, old_ext: str, new_ext: str):

    if not folder_path.exists() or not folder_path.is_dir():
        return

    old_ext = old_ext if old_ext.startswith('.') else f'.{old_ext}'
    new_ext = new_ext if new_ext.startswith('.') else f'.{new_ext}'

    for file_path in folder_path.iterdir():
        if file_path.is_file() and file_path.name.lower().endswith(old_ext.lower()):

            new_file = file_path.with_suffix(new_ext)

            if new_file.exists():
                continue

            file_path.rename(new_file)


def rename_extension(file_path: str, old_ext: str, new_ext: str):
    for root, _, files in os.walk(file_path):
        for f in files:
            if f.endswith(old_ext):
                base = f[:-len(old_ext)]
                os.rename(
                    os.path.join(root, f),
                    os.path.join(root, base + new_ext)
                )


# ✅ plugin-safe
def run(context=None):
    output_folder = BASE_DIR / "模式二輸出"
    rename_extension(str(output_folder), ".zip", ".cbz")


def main():
    run()


if __name__ == "__main__":
    main()