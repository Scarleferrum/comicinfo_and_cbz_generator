import importlib.util
import json
import os
from pathlib import Path
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk

from comicinfo_core.excel_v2_5 import (
    append_comic,
    create_template,
    ensure_excel_columns,
    read_comics,
)
from comicinfo_core.fields_v2_5 import EXCEL_HEADERS, FIELDS
from comicinfo_core.model_v2_5 import ComicMetadata
from comicinfo_core.pipeline_v2_5 import generate_single_cbz
from comicinfo_core.resources_v2_5 import get_hardware_capacity

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    DND_FILES = None
    TkinterDnD = None
    DND_AVAILABLE = False
else:
    DND_AVAILABLE = True

# ====================
# 設定檔
# ====================

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
DEFAULT_CONFIG = {
    "input_bg_color": "#0476D9",
    "max_compression_threads": 2,
    "cpu_core_limit": 2,
    "memory_limit_percent": 40,
}


def load_config():
    if not CONFIG_PATH.exists():
        default = dict(DEFAULT_CONFIG)
        with CONFIG_PATH.open("w", encoding="utf-8") as f:
            json.dump(default, f, indent=4)
        return default
    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        stored_config = json.load(config_file)
    return {**DEFAULT_CONFIG, **stored_config}


def save_config(cfg):
    with CONFIG_PATH.open("w", encoding="utf-8") as config_file:
        json.dump(cfg, config_file, indent=4)


# =========================
# 專案根目錄（標準化）
# =========================
REQUIRED_FILES = [
    BASE_DIR / "config.json",
    BASE_DIR / "comicinfo_core" / "__init__.py",
    BASE_DIR / "comicinfo_core" / "fields_v2_5.py",
    BASE_DIR / "comicinfo_core" / "model_v2_5.py",
    BASE_DIR / "comicinfo_core" / "resources_v2_5.py",
    BASE_DIR / "comicinfo_core" / "xml_v2_5.py",
    BASE_DIR / "comicinfo_core" / "excel_v2_5.py",
    BASE_DIR / "comicinfo_core" / "files_v2_5.py",
    BASE_DIR / "comicinfo_core" / "pipeline_v2_5.py",
    BASE_DIR / "comicinfo_tools" / "comicinfo_v2_5.py",
    BASE_DIR / "comicinfo_tools" / "compress_v2_5.py",
    BASE_DIR / "comicinfo_tools" / "image_extractor_v2_5.py",
    BASE_DIR / "comicinfo_tools" / "rename_extension_v2_5.py",
]


def show_error(message: str):
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("存在錯誤", message)
    root.destroy()


def check_pass(message: str):
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("檢查完成", message)
    root.destroy()


def check_and_create_output_folders(cfg):
    path_mode = cfg.get("path_mode", "relative")

    def resolve(path):
        if path_mode == "absolute":
            return Path(path)
        return BASE_DIR / path

    mode1 = resolve(cfg.get("mode1_output_dir", "模式一輸出"))
    mode2 = resolve(cfg.get("mode2_output_dir", "模式二輸出"))

    mode1.mkdir(parents=True, exist_ok=True)
    mode2.mkdir(parents=True, exist_ok=True)


def check_and_create_excel():
    excel_path = BASE_DIR / "input_v2.5.xlsx"

    if not excel_path.exists():
        create_template(excel_path)
    else:
        ensure_excel_columns(excel_path, EXCEL_HEADERS)


def check_required_files():
    missing_files = [str(f.name) for f in REQUIRED_FILES if not f.exists()]

    if missing_files:
        show_error(
            f"缺少必要檔案：\n{', '.join(missing_files)}\n請重新下載完整工具"
        )
        return False
    return True


# =========================
# 主程式
# =========================
def tools_checker():
    cfg = load_config()
    check_and_create_output_folders(cfg)
    check_and_create_excel()
    if not check_required_files():
        return
    check_pass("檢查完成，所有必要檔案和資料夾都已就緒！")


# ====================
# 圖形化使用者介面
# ====================

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("comicinfo and cbz generator v2.5.0")

        self.config = load_config()
        self.input_bg_color = self.config.get("input_bg_color", "#0476D9")
        self.mode1_output_dir = self.config.get("mode1_output_dir", "模式一輸出")
        self.mode2_output_dir = self.config.get("mode2_output_dir", "模式二輸出")
        self.path_mode = self.config.get("path_mode", "relative")
        self.hardware_capacity = get_hardware_capacity()
        self.resource_limits = {
            "max_compression_threads": self._bounded_setting(
                self.config.get("max_compression_threads"),
                default=2,
                maximum=self.hardware_capacity.logical_cpus,
            ),
            "cpu_core_limit": self._bounded_setting(
                self.config.get("cpu_core_limit"),
                default=2,
                maximum=self.hardware_capacity.physical_cpus,
            ),
            "memory_limit_percent": self._bounded_setting(
                self.config.get("memory_limit_percent", 40),
                default=40,
                maximum=100,
            ),
        }
        self.resource_limits["memory_limit_percent"] = min(
            100,
            max(
                10,
                round(self.resource_limits["memory_limit_percent"] / 10) * 10,
            ),
        )
        self.config.update(self.resource_limits)

        self.entries = {}

        # ====================
        # 模式一
        # ====================
        self.frame1 = tk.LabelFrame(root, text="模式一：生成單一CBZ（支援拖放）")
        self.frame1.pack(fill="both", padx=10, pady=5)
        self.frame1.columnconfigure(tuple(range(1, 5)), weight=1)

        fields = {field.label: field.key for field in FIELDS}

        self.entries = {}
        labels = list(fields.keys())
        # 兩欄排版
        for i in range(0, len(labels), 2):
            r = i // 2

            l1 = labels[i]
            l2 = labels[i + 1] if i + 1 < len(labels) else None

            # 左欄
            tk.Label(self.frame1, text=l1).grid(row=r, column=0)
            e1 = tk.Entry(self.frame1, width=25, bg=self.input_bg_color)
            e1.grid(row=r, column=1)

            self.entries[fields[l1]] = e1

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
        if DND_AVAILABLE:
            self.drop_area = tk.Label(
                self.frame1,
                text="拖放到此處",
                relief="ridge",
                width=50,
                height=3,
            )
            self.drop_area.grid(row=last_row + 1, column=0, columnspan=4, pady=5)
        else:
            self.drop_area = tk.Label(
                self.frame1,
                text="拖放功能不可用，請先安裝依賴模組 tkinterdnd2",
                relief="ridge",
                width=50,
                height=3,
            )
            self.drop_area.grid(row=last_row + 1, column=0, columnspan=4, pady=5)

        row_offset = last_row + 2

        tk.Label(self.frame1, text="來源路徑").grid(row=row_offset, column=0)
        self.input_path = tk.Entry(self.frame1, width=60, bg=self.input_bg_color)
        self.input_path.grid(row=row_offset, column=1, columnspan=10)

        actions = tk.Frame(self.frame1)
        actions.grid(row=row_offset + 1, column=1, columnspan=4, sticky="ew")
        actions.columnconfigure(tuple(range(3)), weight=1, uniform="mode1_actions")
        mode1_buttons = [
            ("選擇壓縮檔", self.select_file),
            ("選擇資料夾", self.select_folder),
            ("執行模式一", self.run_mode1),
            ("匯入Excel資料", self.import_excel_record),
            ("寫入Excel資料", self.write_excel_record),
            ("清除輸入", self.clear_all),
        ]
        for index, (text, command) in enumerate(mode1_buttons):
            tk.Button(actions, text=text, command=command).grid(
                row=index // 3,
                column=index % 3,
                sticky="ew",
                padx=3,
                pady=3,
            )

        # ====================
        # 啟用拖放
        # ====================

        if DND_AVAILABLE:
            self.drop_area.drop_target_register(DND_FILES)
            self.drop_area.dnd_bind("<<Drop>>", self.on_drop)

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

        tk.Button(bottom, text="設定", command=self.open_settings).pack(side="left")

    # =====================
    # 拖放
    # =====================
    @staticmethod
    def _bounded_setting(value, default: int, maximum: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = default
        return min(max(parsed, 1), maximum)

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
                "scripts": ["comicinfo_tools/comicinfo_v2_5.py"],
            },
            {
                "name": "批量壓縮並修改副檔名",
                "scripts": [
                    "comicinfo_tools/compress_v2_5.py",
                    "comicinfo_tools/rename_extension_v2_5.py",
                ],
            },
        ]

        extension_buttons = tk.Frame(self.frame2)
        extension_buttons.pack(fill="x")
        extension_buttons.columnconfigure((0, 1), weight=1, uniform="mode2_extensions")
        for column, ext in enumerate(extensions):
            tk.Button(
                extension_buttons,
                text=ext["name"],
                command=lambda e=ext: self.run_extension(e),
            ).grid(row=0, column=column, sticky="ew", padx=3, pady=3)

    def run_extension(self, ext):
        try:
            base = str(BASE_DIR)

            # ⭐ 統一 context（核心）
            context = {
                "base_dir": base,
                "output_dir": self.resolve_path(self.mode2_output_dir),
                "excel_path": str(BASE_DIR / "input_v2.5.xlsx"),
                **self.resource_limits,
            }

            scripts = ext.get("scripts", [])
            results = []

            for script in scripts:
                script_path = os.path.join(base, script)

                if not os.path.exists(script_path):
                    raise FileNotFoundError(script_path)

                module_name = Path(script).stem

                spec = importlib.util.spec_from_file_location(
                    module_name,
                    script_path,
                )
                if spec is None or spec.loader is None:
                    raise ImportError(f"無法載入模組: {script_path}")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # ⭐ 只允許 run(context)
                if hasattr(module, "run"):
                    results.append(module.run(context))
                else:
                    raise AttributeError(f"{script} 缺少 run(context) 入口")

            failures = [
                result
                for result in results
                if isinstance(result, dict)
                and result.get("status") not in (None, "success")
            ]
            if failures:
                messagebox.showwarning(
                    "部分作業失敗",
                    "批次處理未全部完成：\n"
                    + "\n".join(
                        str(result.get("details", result))
                        for result in failures
                    ),
                )
                return

            if ext["name"] == "從Excel批量輸出xml":
                messagebox.showinfo(
                    "完成",
                    f"從 Excel 批量輸出 XML 至「{self.mode2_output_dir}」資料夾",
                )
            if ext["name"] == "批量壓縮並修改副檔名":
                messagebox.showinfo(
                    "完成",
                    f"在「{self.mode2_output_dir}」資料夾批量壓縮並修改副檔名",
                )

        except Exception as exc:
            messagebox.showerror("錯誤", str(exc))

    # =====================
    # 模式一
    # =====================
    def run_mode1(self):
        try:
            data = ComicMetadata({k: e.get().strip() for k, e in self.entries.items()})
            src = self.input_path.get().strip()

            if not data.get("Title") or not src:
                raise ValueError("Title 或來源不可為空")
            output_root = self.resolve_path(self.mode1_output_dir)

            generate_single_cbz(src, data, output_root)
            messagebox.showinfo(
                "完成",
                f"CBZ 已生成至「{self.mode1_output_dir}」資料夾",
            )

        except Exception as exc:
            messagebox.showerror("錯誤", str(exc))

    def import_excel_record(self):
        path = filedialog.askopenfilename(
            title="選擇漫畫資料 Excel",
            filetypes=[("Excel 活頁簿", "*.xlsx *.xlsm"), ("所有檔案", "*.*")],
        )
        if not path:
            return
        try:
            records = read_comics(path)
            if not records:
                raise ValueError("工作表中沒有包含 Title 的漫畫資料列")
            if len(records) == 1:
                self.load_comic_to_form(records[0])
                return

            picker = tk.Toplevel(self.root)
            picker.title("選擇漫畫資料")
            picker.transient(self.root)
            listing = tk.Listbox(picker, width=72, height=min(18, len(records)))
            listing.pack(fill="both", expand=True, padx=10, pady=10)
            for comic in records:
                listing.insert(
                    tk.END,
                    f"{comic.get('Title')} | {comic.get('Series')} | "
                    f"{comic.get('Number')}",
                )

            def load_selected(_event=None):
                selection = listing.curselection()
                if not selection:
                    return
                self.load_comic_to_form(records[selection[0]])
                picker.destroy()

            tk.Button(picker, text="載入選取資料", command=load_selected).pack(pady=(0, 10))
            listing.bind("<Double-Button-1>", load_selected)
        except Exception as exc:
            messagebox.showerror("Excel 匯入錯誤", str(exc))

    def write_excel_record(self):
        try:
            data = ComicMetadata({key: entry.get().strip() for key, entry in self.entries.items()})
            if not data.get("Title"):
                raise ValueError("Title 不可為空")
            excel_path = BASE_DIR / "input_v2.5.xlsx"
            row_number = append_comic(excel_path, data)
            messagebox.showinfo(
                "Excel 寫入完成",
                f"已寫入第一張工作表第 {row_number} 列：{excel_path.name}",
            )
        except Exception as exc:
            messagebox.showerror("Excel 寫入錯誤", str(exc))

    def load_comic_to_form(self, comic):
        values = (
            comic.as_dict()
            if isinstance(comic, ComicMetadata)
            else ComicMetadata(comic).as_dict()
        )
        for key, entry in self.entries.items():
            entry.delete(0, tk.END)
            entry.insert(0, values.get(key, ""))

    # =====================
    # utils
    # =====================
    def resolve_path(self, path):
        """Resolve configured paths relative to the application directory."""
        if self.path_mode == "absolute":
            return Path(path)
        return BASE_DIR / path

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
        win.transient(self.root)

        def close_settings():
            win.destroy()
            self.root.after_idle(restore_main_window)

        def restore_main_window():
            if self.root.winfo_exists():
                self.root.lift()
                self.root.update_idletasks()

        win.protocol("WM_DELETE_WINDOW", close_settings)

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

        general = tk.LabelFrame(win, text="一般設定")
        general.pack(fill="x", padx=10, pady=10)
        general.columnconfigure(1, weight=1)

        tk.Button(general, text="執行簡單檢查", command=tools_checker).grid(
            row=0, column=1, sticky="e", padx=8, pady=4
        )
        tk.Label(general, text="環境與 Excel 檢查").grid(
            row=0, column=0, sticky="w", padx=8, pady=4
        )

        tk.Label(general, text="輸入框顏色").grid(
            row=1, column=0, sticky="w", padx=8, pady=4
        )
        tk.Button(general, text="選擇顏色", command=choose_color).grid(
            row=1, column=1, sticky="e", padx=8, pady=4
        )

        tk.Label(general, text="路徑模式").grid(
            row=2, column=0, sticky="w", padx=8, pady=4
        )
        path_mode_buttons = tk.Frame(general)
        path_mode_buttons.grid(row=2, column=1, sticky="e", padx=8, pady=4)
        tk.Button(
            path_mode_buttons,
            text="相對路徑（專案內）",
            command=set_relative,
        ).pack(side="left", padx=(0, 4))
        tk.Button(
            path_mode_buttons,
            text="完整路徑（自訂位置）",
            command=set_absolute,
        ).pack(side="left")

        tk.Label(general, text="模式一輸出路徑").grid(
            row=3, column=0, sticky="w", padx=8, pady=4
        )
        tk.Button(
            general,
            text="選擇輸出路徑",
            command=choose_mode1_dir,
        ).grid(row=3, column=1, sticky="e", padx=8, pady=4)

        tk.Label(general, text="模式二輸出路徑").grid(
            row=4, column=0, sticky="w", padx=8, pady=4
        )
        tk.Button(
            general,
            text="選擇輸出路徑",
            command=choose_mode2_dir,
        ).grid(row=4, column=1, sticky="e", padx=8, pady=4)

        limits = tk.LabelFrame(win, text="硬體資源限制")
        limits.pack(fill="x", padx=10, pady=10)
        limit_variables = {
            "max_compression_threads": tk.StringVar(
                value=str(self.resource_limits["max_compression_threads"])
            ),
            "cpu_core_limit": tk.StringVar(
                value=str(self.resource_limits["cpu_core_limit"])
            ),
            "memory_limit_percent": tk.StringVar(
                value=f"{self.resource_limits['memory_limit_percent']}%"
            ),
        }
        limit_rows = (
            (
                "最大同時壓縮線程數"
                f"（邏輯 CPU 上限：{self.hardware_capacity.logical_cpus}）",
                "max_compression_threads",
                self.hardware_capacity.logical_cpus,
            ),
            (
                "CPU 核心調用數"
                f"（物理核心上限：{self.hardware_capacity.physical_cpus}）",
                "cpu_core_limit",
                self.hardware_capacity.physical_cpus,
            ),
            (
                "記憶體調用量限制",
                "memory_limit_percent",
                tuple(f"{value}%" for value in range(10, 101, 10)),
            ),
        )
        for row, (label, key, choices) in enumerate(limit_rows):
            if isinstance(choices, int):
                choices = tuple(range(1, choices + 1))
            tk.Label(limits, text=label).grid(
                row=row,
                column=0,
                sticky="w",
                padx=8,
                pady=3,
            )
            ttk.Combobox(
                limits,
                values=choices,
                textvariable=limit_variables[key],
                state="readonly",
                width=8,
            ).grid(row=row, column=1, sticky="e", padx=8, pady=3)

        if self.hardware_capacity.physical_memory_bytes is not None:
            memory_gib = self.hardware_capacity.physical_memory_bytes / (1024**3)
            memory_description = f"偵測到物理記憶體：{memory_gib:.1f} GiB"
        else:
            memory_description = "無法自動偵測物理記憶體總量"
        tk.Label(limits, text=memory_description).grid(
            row=len(limit_rows),
            column=0,
            columnspan=2,
            sticky="w",
            padx=8,
            pady=3,
        )
        tk.Label(
            limits,
            text="記憶體百分比為軟性預算，會依程式用量與系統可用記憶體調整並行數。",
            wraplength=420,
            justify="left",
        ).grid(
            row=len(limit_rows) + 1,
            column=0,
            columnspan=2,
            sticky="w",
            padx=8,
            pady=3,
        )

        def save_resource_limits():
            try:
                values = {
                    key: int(variable.get().rstrip("%"))
                    for key, variable in limit_variables.items()
                }
            except ValueError:
                messagebox.showerror("設定錯誤", "硬體限制必須是整數")
                return

            if not (
                1
                <= values["max_compression_threads"]
                <= self.hardware_capacity.logical_cpus
            ):
                messagebox.showerror(
                    "設定錯誤",
                    f"同時壓縮線程數必須介於 1 至 {self.hardware_capacity.logical_cpus}",
                )
                return
            if not (
                1
                <= values["cpu_core_limit"]
                <= self.hardware_capacity.physical_cpus
            ):
                messagebox.showerror(
                    "設定錯誤",
                    f"CPU 核心調用數必須介於 1 至 {self.hardware_capacity.physical_cpus}",
                )
                return
            if values["memory_limit_percent"] not in range(10, 101, 10):
                messagebox.showerror(
                    "設定錯誤",
                    "記憶體百分比必須為 10% 至 100%，並以 10% 為級距",
                )
                return

            self.resource_limits.update(values)
            self.config.update(values)
            save_config(self.config)
            messagebox.showinfo("設定", "硬體資源限制已儲存")

        tk.Button(
            limits,
            text="儲存硬體限制",
            command=save_resource_limits,
        ).grid(row=len(limit_rows) + 2, column=0, columnspan=2, pady=8)

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
