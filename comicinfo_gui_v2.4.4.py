import os
import shutil
import tkinter as tk
from tkinter import Tk, filedialog, messagebox, colorchooser
import json
import xml.etree.ElementTree as ET
import importlib.util
from pathlib import Path
from openpyxl import Workbook
import re

# ====================
# 拖放支援
# ====================

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except:
    DND_AVAILABLE = False

# ====================
# 從tools資料夾導入功能
# ====================

from tools.image_extractor.v2 import extract_input, collect_images
from tools.rename_extension.v2 import rename_extension
from tools.compress.v2 import zip_folder_gui

# ====================
# 模式一輸出comicinfo.xml
# ====================

def generate_xml(folder, data):
    root = ET.Element("ComicInfo", {
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:noNamespaceSchemaLocation": "https://raw.githubusercontent.com/anansi-project/comicinfo/main/schema/v2.0/ComicInfo.xsd"
    })

    def add(tag, default=""):
        el = ET.SubElement(root, tag)
        val = data.get(tag, "")
        el.text = val if val != "" else ""

    add("Title")
    add("Series")
    add("Number")
    add("Count")
    add("Summary")
    add("Year")
    add("Month")
    add("Day")
    add("Writer")
    add("Penciller")
    add("Inker")
    add("Colorist")
    add("Letterer")
    add("CoverArtist")
    add("Editor")
    add("Publisher")
    add("Genre")
    add("Tags")
    add("Web")
    add("PageCount")
    add("LanguageISO")
    add("Format")
    add("BlackAndWhite")
    add("Manga")
    add("Characters")
    add("Teams")
    add("AgeRating")

    try:
        ET.indent(root, space="    ")
    except AttributeError:
        pass

    tree = ET.ElementTree(root)
    tree.write(
        os.path.join(folder, "comicinfo.xml"),
        encoding="utf-8",
        xml_declaration=True,
        short_empty_elements=False
    )

# ====================
# 設定檔
# ====================

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    if not os.path.exists(CONFIG_PATH):
        default = {"input_bg_color": "#0476D9"}
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=4)
        return default
    return json.load(open(CONFIG_PATH, "r", encoding="utf-8"))

def save_config(cfg):
    json.dump(cfg, open(CONFIG_PATH, "w", encoding="utf-8"), indent=4)

# =========================
# 專案根目錄（標準化）
# =========================
BASE_DIR = Path(__file__).resolve().parents[0]

# =========================
# 必要檔案
# =========================
REQUIRED_FILES = [
    BASE_DIR / "config.json",
    BASE_DIR / "tools" / "comicinfo" / "v2_mode_1.py",
    BASE_DIR / "tools" / "comicinfo" / "v2_mode_2.py",
    BASE_DIR / "tools" / "compress" / "v2.py",
    BASE_DIR / "tools" / "image_extractor" / "v2.py",
    BASE_DIR / "tools" / "rename_extension" / "v2.py"
]

# =========================
# Excel 欄位
# =========================
EXCEL_HEADERS = [
    "Title", "Series", "Number", "Count", "Summary",
    "Year", "Month", "Day", "Writer", "Publisher",
    "Genre", "Tags", "Web", "LanguageISO", "Format",
    "BlackAndWhite", "Manga", "Characters", "Teams", "AgeRating"
]

def show_error(message: str):
    root = Tk()
    root.withdraw()
    messagebox.showerror("存在錯誤", message)
    root.destroy()

def check_pass(message: str):
    root = Tk()
    root.withdraw()
    messagebox.showinfo("檢查完成", message)
    root.destroy()

def check_and_create_output_folders(cfg):
    base = BASE_DIR

    path_mode = cfg.get("path_mode", "relative")

    def resolve(path):
        if path_mode == "absolute":
            return Path(path)
        return base / path

    mode1 = resolve(cfg.get("mode1_output_dir", "模式一輸出"))
    mode2 = resolve(cfg.get("mode2_output_dir", "模式二輸出"))

    mode1.mkdir(parents=True, exist_ok=True)
    mode2.mkdir(parents=True, exist_ok=True)

def check_and_create_excel():
    excel_path = BASE_DIR / "input_v2.4.xlsx"

    if not excel_path.exists():
        wb = Workbook()
        ws = wb.active
        ws.append(EXCEL_HEADERS)
        wb.save(excel_path)
    else:
        pass

def check_required_files():
    missing_files = [str(f.name) for f in REQUIRED_FILES if not f.exists()]

    if missing_files:
        show_error(
            f"缺少必要檔案：\n{', '.join(missing_files)}\n請重新下載完整工具"
        )
    else:
        pass

# =========================
# 主程式
# =========================
def tools_checker():
    cfg = load_config()
    check_and_create_output_folders(cfg)
    check_and_create_excel()
    check_required_files()
    check_pass("檢查完成，所有必要檔案和資料夾都已就緒！")

# =========================
# 梳理檔名
# =========================

def sanitize_filename(name: str) -> str:
    """
    移除 Windows 不允許字元 + 控制字元
    """
    return re.sub(r'[<>:"/\\|?*\n\r\t]', '', name).strip()

# ====================
# 圖形化使用者介面
# ====================

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("comicinfo and cbz generator v2.4.4")

        self.config = load_config()
        self.input_bg_color = self.config.get("input_bg_color", "#0476D9")
        self.mode1_output_dir = self.config.get("mode1_output_dir", "模式一輸出")
        self.mode2_output_dir = self.config.get("mode2_output_dir", "模式二輸出")
        self.path_mode = self.config.get("path_mode", "relative")

        self.entries = {}

        # ====================
        # 模式一
        # ====================
        self.frame1 = tk.LabelFrame(root, text="模式一：生成單一CBZ（支援拖放）")
        self.frame1.pack(fill="both", padx=10, pady=5)

        fields = {
            "標題": "Title",
            "系列": "Series",
            "總集數": "Number",
            "總數": "Count",
            "摘要": "Summary",
            "年份": "Year",
            "月份": "Month",
            "日期": "Day",
            "作者": "Writer",
            "出版社": "Publisher",
            "類型": "Genre",
            "標籤": "Tags",
            "網站": "Web",
            "語言": "LanguageISO",
            "格式": "Format",
            "黑白": "BlackAndWhite",
            "漫畫方向": "Manga",
            "角色": "Characters",
            "團隊": "Teams",
            "分級": "AgeRating"
        }

        self.entries = {}
        labels = list(fields.keys())
        # 兩欄排版


        for i in range(0, len(labels), 2):
            r = i // 2

            l1 = labels[i]
            l2 = labels[i+1] if i+1 < len(labels) else None

            # 左欄
            tk.Label(self.frame1, text=l1).grid(row=r, column=0)
            e1 = tk.Entry(self.frame1, width=25, bg=self.input_bg_color)
            e1.grid(row=r, column=1)

            self.entries[fields[l1]] = e1   # ⭐ 關鍵：存 key

            # 右欄
            if l2:
                tk.Label(self.frame1, text=l2).grid(row=r, column=2)
                e2 = tk.Entry(self.frame1, width=25, bg=self.input_bg_color)
                e2.grid(row=r, column=3)

                self.entries[fields[l2]] = e2
        
        last_row = (len(fields) + 1) // 2

        # ===== 拖放區 =====
        tk.Label(self.frame1, text="拖放 ZIP 或資料夾到下方區域").grid(
            row=last_row, column=0, columnspan=2
        )
        if DND_AVAILABLE == True:
            self.drop_area = tk.Label(self.frame1,text="拖放到此處",relief="ridge",width=50,height=3)
            self.drop_area.grid(row=last_row+1, column=0, columnspan=4, pady=5)
        else:
            self.drop_area = tk.Label(self.frame1,text="拖放功能不可用，請先安裝依賴模組tkinterdnd2",relief="ridge",width=50,height=3)
            self.drop_area.grid(row=last_row+1, column=0, columnspan=4, pady=5)

        row_offset = last_row + 2

        tk.Label(self.frame1, text="來源路徑").grid(row=row_offset, column=0)
        self.input_path = tk.Entry(self.frame1, width=60, bg=self.input_bg_color)
        self.input_path.grid(row=row_offset, column=1, columnspan=10)

        tk.Button(self.frame1, text="選擇壓縮檔", command=self.select_file).grid(row=row_offset+1, column=1, columnspan=1)
        tk.Button(self.frame1, text="選擇資料夾", command=self.select_folder).grid(row=row_offset+1, column=2)
        tk.Button(self.frame1, text="執行模式一", command=self.run_mode1).grid(row=row_offset+1, column=3)

        # ====================
        # 啟用拖放
        # ====================

        if DND_AVAILABLE:
            self.drop_area.drop_target_register(DND_FILES)
            self.drop_area.dnd_bind('<<Drop>>', self.on_drop)

        # ====================
        # 模式二
        # ====================
        self.frame2 = tk.LabelFrame(root, text="模式二：批量模式")
        self.frame2.pack(fill="both", padx=10, pady=5)

        self.init_mode2_extensions()

        # =====================
        # 底部按鈕
        # =====================
        bottom = tk.Frame(root)
        bottom.pack(pady=10)

        tk.Button(bottom, text="清除輸入", command=self.clear_all).pack(side="left")
        tk.Button(bottom, text="設定", command=self.open_settings).pack(side="left")
        tk.Button(bottom, text="簡單檢查", command=tools_checker).pack(side="left")

    # =====================
    # 拖放
    # =====================
    def on_drop(self, event):
        files = self.root.tk.splitlist(event.data)

        if not files:
            return

        path = files[0].strip()

        # 清掉 file:///
        if path.startswith("file:///"):
            path = path.replace("file:///", "").replace("/", "\\")

        self.input_path.delete(0, tk.END)
        self.input_path.insert(0, path)

    # =====================
    # 模式二 extensions
    # =====================
    def init_mode2_extensions(self):

        extensions = [
            {
                "name": "從Excel批量輸出xml",
                "scripts": [
                    "tools/comicinfo/v2_mode_2.py"
                    ]
            },
            {
                "name": "批量壓縮並修改副檔名",
                "scripts": [
                    "tools/compress/v2.py",
                    "tools/rename_extension/v2.py"
                    ]
            }
        ]

        for ext in extensions:
            tk.Button(
                self.frame2,
                text=ext["name"],
                command=lambda e=ext: self.run_extension(e)
            ).pack(pady=3)

    def run_extension(self, ext):
        try:
            base = os.path.dirname(__file__)

            # ⭐ 統一 context（核心）
            context = {
                "base_dir": base,
                "output_dir": self.resolve_path(self.mode2_output_dir),
                "excel_path": os.path.join(base, "input_v2.4.xlsx")
            }

            scripts = ext.get("scripts", [])

            for script in scripts:
                script_path = os.path.join(base, script)

                if not os.path.exists(script_path):
                    raise FileNotFoundError(script_path)

                module_name = os.path.basename(script).replace(".py", "")

                spec = importlib.util.spec_from_file_location(module_name, script_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # ⭐ 只允許 run(context)
                if hasattr(module, "run"):
                    module.run(context)
                else:
                    raise Exception(f"{script} 缺少 run(context) 入口")

            if ext["name"] == "從Excel批量輸出xml":
                messagebox.showinfo("完成", "從Excel批量輸出xml至「"+self.mode2_output_dir+"」資料夾")
            if ext["name"] == "批量壓縮並修改副檔名":
                messagebox.showinfo("完成", "在「"+self.mode2_output_dir+"」資料夾批量壓縮並修改副檔名")

        except Exception as e:
            messagebox.showerror("錯誤", str(e))

    # =====================
    # 模式一
    # =====================
    def run_mode1(self):
        try:
            data = {k: e.get().strip() for k, e in self.entries.items()}
            title = data.get("Title", "").strip()
            src = self.input_path.get().strip()

            title = sanitize_filename(title)

            if not title or not src:
                raise Exception("Title或來源不可為空")

            base = os.path.dirname(__file__)
            output_root = self.resolve_path(self.mode1_output_dir)
            os.makedirs(output_root, exist_ok=True)

            target = os.path.join(output_root, title)
            os.makedirs(target, exist_ok=True)

            temp = extract_input(src)
            imgs = collect_images(temp)

            for img in imgs:
                shutil.copy(img, os.path.join(target, os.path.basename(img)))
            
            generate_xml(target, data)

            zip_folder_gui(target, output_root)
            rename_extension(output_root, ".zip", ".cbz")

            shutil.rmtree(temp)


            messagebox.showinfo("完成", "CBZ已生成至工具內「"+self.mode1_output_dir+"」資料夾")

        except Exception as e:
            messagebox.showerror("錯誤", str(e))

    # =====================
    # utils
    # =====================
    def resolve_path(self, path):
        """
        根據 path_mode 決定是否使用完整路徑
        """
        if self.path_mode == "absolute":
            return path
        else:
            base = os.path.dirname(__file__)
            return os.path.join(base, path)

    def select_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.input_path.delete(0, tk.END)
            self.input_path.insert(0, path)
    
    def select_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.input_path.delete(0, tk.END)
            self.input_path.insert(0, path)

    def clear_all(self):
        for e in self.entries.values():
            e.delete(0, tk.END)
        self.input_path.delete(0, tk.END)

    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("設定")

        def choose_color():
            color = colorchooser.askcolor()[1]
            if color:
                self.input_bg_color = color
                self.config["input_bg_color"] = color
                save_config(self.config)

                for e in self.entries.values():
                    e.config(bg=color)
                self.input_path.config(bg=color)
        
        def set_relative():
            self.path_mode = "relative"
            self.config["path_mode"] = "relative"
            save_config(self.config)
            messagebox.showinfo("設定", "已切換為相對路徑模式")

        def set_absolute():
            self.path_mode = "absolute"
            self.config["path_mode"] = "absolute"
            save_config(self.config)
            messagebox.showinfo("設定", "已切換為完整路徑模式")
        
        def choose_mode1_dir():
            path = filedialog.askdirectory()
            if path:
                if self.path_mode == "absolute":
                    self.mode1_output_dir = path
                else:
                    self.mode1_output_dir = os.path.basename(path)

                self.config["mode1_output_dir"] = self.mode1_output_dir
                save_config(self.config)

        def choose_mode2_dir():
            path = filedialog.askdirectory()
            if path:
                if self.path_mode == "absolute":
                    self.mode2_output_dir = path
                else:
                    self.mode2_output_dir = os.path.basename(path)

                self.config["mode2_output_dir"] = self.mode2_output_dir
                save_config(self.config)


        tk.Button(win, text="輸入框顏色", command=choose_color).pack()
        tk.Label(win, text="路徑模式").pack(pady=5)
        tk.Button(win, text="相對路徑（專案內）", command=set_relative).pack()
        tk.Button(win, text="完整路徑（自訂位置）", command=set_absolute).pack()
        tk.Label(win, text="自訂輸出路徑").pack(pady=5)
        tk.Button(win, text="選擇模式一輸出路徑", command=choose_mode1_dir).pack()
        tk.Button(win, text="選擇模式二輸出路徑", command=choose_mode2_dir).pack()
    

    def show_error(message: str):
        root = Tk()
        root.withdraw()
        messagebox.showerror("錯誤", message)
        root.destroy()

# =====================
# main
# =====================
if __name__ == "__main__":
    if DND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()

    App(root)
    root.mainloop()