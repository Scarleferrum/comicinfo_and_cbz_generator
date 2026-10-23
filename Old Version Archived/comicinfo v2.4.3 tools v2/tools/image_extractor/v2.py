import os
import shutil
import zipfile


def extract_input(src_path, temp_dir="temp_extract"):
    """
    解壓 zip 或複製資料夾到暫存區
    """
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    os.makedirs(temp_dir)

    if zipfile.is_zipfile(src_path):
        with zipfile.ZipFile(src_path, 'r') as z:
            z.extractall(temp_dir)
    else:
        shutil.copytree(src_path, temp_dir, dirs_exist_ok=True)

    return temp_dir


def collect_images(src_dir):
    """
    收集圖片檔案（排序後）
    """
    images = []
    for root, _, files in os.walk(src_dir):
        for f in files:
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                images.append(os.path.join(root, f))

    return sorted(images)