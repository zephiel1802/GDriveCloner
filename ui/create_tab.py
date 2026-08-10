"""
Create Tab — UI to create a new temp shared folder.
"""
import threading
import datetime
import customtkinter as ctk
from ui.folder_browser import FolderBrowserDialog
from services import config as cfg


ACCENT    = "#4F8EF7"
BG        = "#1A1D2E"
CARD      = "#242840"
CARD2     = "#1E2238"
TEXT      = "#E8EAF6"
SUBTEXT   = "#9095B8"
SUCCESS   = "#4CAF7D"
HOVER     = "#2E3255"
BORDER    = "#3A3F6B"
ERROR     = "#FF6B6B"

DURATION_OPTIONS = {
    "1 giờ": 1,
    "6 giờ": 6,
    "12 giờ": 12,
    "24 giờ": 24,
    "48 giờ": 48,
    "Tuỳ chỉnh...": -1,
}


class CreateTab(ctk.CTkFrame):
    def __init__(self, parent, get_drive_service, on_share_created):
        super().__init__(parent, fg_color=BG)
        self.get_drive_service = get_drive_service
        self.on_share_created = on_share_created  # callback when done
        self._build_ui()

    def _build_ui(self):
        # ── Scrollable content ─────────────────────────────
        scroll = ctk.CTkScrollableFrame(self, fg_color=BG, scrollbar_button_color=CARD)
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # ── Title ──────────────────────────────────────────
        ctk.CTkLabel(
            scroll, text="✨  Tạo Link Share Tạm",
            font=("Inter", 20, "bold"), text_color=TEXT,
        ).pack(anchor="w", padx=28, pady=(24, 4))
        ctk.CTkLabel(
            scroll, text="Copy file từ thư mục nguồn, tạo link share và tự động xóa sau thời hạn.",
            font=("Inter", 12), text_color=SUBTEXT,
        ).pack(anchor="w", padx=28, pady=(0, 20))

        # ── Source folder card ─────────────────────────────
        self._make_section_label(scroll, "📂  Thư mục nguồn")
        src_card = ctk.CTkFrame(scroll, fg_color=CARD, corner_radius=12)
        src_card.pack(fill="x", padx=24, pady=(4, 16))

        src_row = ctk.CTkFrame(src_card, fg_color="transparent")
        src_row.pack(fill="x", padx=16, pady=14)

        self._src_label = ctk.CTkLabel(
            src_row,
            text=f"📁  {cfg.get('source_folder_name')}",
            font=("Inter", 13), text_color=TEXT, anchor="w",
        )
        self._src_label.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            src_row, text="Thay đổi", width=90, height=30,
            fg_color=ACCENT, hover_color="#3A70D4",
            text_color="white", font=("Inter", 12),
            command=self._browse_source_folder,
        ).pack(side="right")

        # File count label
        self._file_count_label = ctk.CTkLabel(
            src_card, text="",
            font=("Inter", 11), text_color=SUBTEXT, anchor="w",
        )
        self._file_count_label.pack(anchor="w", padx=16, pady=(0, 10))

        self._refresh_file_count()

        # ── Folder name ────────────────────────────────────
        self._make_section_label(scroll, "📝  Tên thư mục tạm")
        name_card = ctk.CTkFrame(scroll, fg_color=CARD, corner_radius=12)
        name_card.pack(fill="x", padx=24, pady=(4, 16))

        self._name_var = ctk.StringVar(value=self._default_name())
        name_entry = ctk.CTkEntry(
            name_card, textvariable=self._name_var,
            font=("Inter", 13), text_color=TEXT,
            fg_color=CARD2, border_color=BORDER, height=40,
        )
        name_entry.pack(fill="x", padx=14, pady=12)

        # ── Duration ───────────────────────────────────────
        self._make_section_label(scroll, "⏱  Thời hạn tự xóa")
        dur_card = ctk.CTkFrame(scroll, fg_color=CARD, corner_radius=12)
        dur_card.pack(fill="x", padx=24, pady=(4, 16))

        btn_row = ctk.CTkFrame(dur_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=12)

        self._duration_var = ctk.IntVar(value=cfg.get("default_duration_hours"))
        self._dur_buttons = {}

        for label, hours in DURATION_OPTIONS.items():
            if label == "Tuỳ chỉnh...":
                continue
            btn = ctk.CTkButton(
                btn_row, text=label, width=72, height=32,
                fg_color=CARD2, hover_color=HOVER,
                border_color=ACCENT if hours == self._duration_var.get() else BORDER,
                border_width=2,
                text_color=ACCENT if hours == self._duration_var.get() else SUBTEXT,
                font=("Inter", 12),
                command=lambda h=hours, lbl=label: self._select_duration(h, lbl),
            )
            btn.pack(side="left", padx=4)
            self._dur_buttons[label] = btn

        # Custom hours row
        custom_row = ctk.CTkFrame(dur_card, fg_color="transparent")
        custom_row.pack(fill="x", padx=14, pady=(0, 12))
        ctk.CTkLabel(
            custom_row, text="Hoặc nhập số giờ:",
            font=("Inter", 12), text_color=SUBTEXT,
        ).pack(side="left")
        self._custom_hours_var = ctk.StringVar()
        ctk.CTkEntry(
            custom_row, textvariable=self._custom_hours_var,
            width=70, height=30, placeholder_text="72",
            fg_color=CARD2, border_color=BORDER,
            text_color=TEXT, font=("Inter", 12),
        ).pack(side="left", padx=8)
        ctk.CTkLabel(
            custom_row, text="giờ",
            font=("Inter", 12), text_color=SUBTEXT,
        ).pack(side="left")

        # ── Action button ──────────────────────────────────
        self._create_btn = ctk.CTkButton(
            scroll,
            text="🚀  Tạo & Share ngay",
            height=48, font=("Inter", 15, "bold"),
            fg_color=ACCENT, hover_color="#3A70D4",
            text_color="white", corner_radius=12,
            command=self._start_create,
        )
        self._create_btn.pack(fill="x", padx=24, pady=(8, 16))

        # ── Progress / Result area ─────────────────────────
        self._progress_frame = ctk.CTkFrame(scroll, fg_color=CARD, corner_radius=12)
        self._progress_frame.pack(fill="x", padx=24, pady=(0, 24))
        self._progress_frame.pack_forget()

        self._progress_label = ctk.CTkLabel(
            self._progress_frame, text="",
            font=("Inter", 13), text_color=SUBTEXT, wraplength=420,
        )
        self._progress_label.pack(padx=16, pady=(14, 4))

        self._progressbar = ctk.CTkProgressBar(
            self._progress_frame, fg_color=CARD2,
            progress_color=ACCENT, height=6,
        )
        self._progressbar.set(0)

        self._link_var = ctk.StringVar()
        self._link_entry = ctk.CTkEntry(
            self._progress_frame, textvariable=self._link_var,
            font=("Inter", 12), text_color=TEXT,
            fg_color=CARD2, border_color=BORDER, state="readonly", height=36,
        )

        self._copy_btn = ctk.CTkButton(
            self._progress_frame, text="📋  Copy Link",
            height=36, font=("Inter", 12, "bold"),
            fg_color=SUCCESS, hover_color="#3A8C60",
            text_color="white",
            command=self._copy_link,
        )

    # ──────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────

    def _make_section_label(self, parent, text: str):
        ctk.CTkLabel(
            parent, text=text,
            font=("Inter", 12, "bold"), text_color=SUBTEXT,
        ).pack(anchor="w", padx=28, pady=(0, 2))

    def _default_name(self) -> str:
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        prefix = cfg.get("temp_folder_prefix")
        return f"{prefix}{now}"

    def _browse_source_folder(self):
        ds = self.get_drive_service()
        if not ds:
            return
        dlg = FolderBrowserDialog(self.winfo_toplevel(), ds)
        self.winfo_toplevel().wait_window(dlg)
        if dlg.result:
            folder_id, folder_name = dlg.result
            cfg.set_value("source_folder_id", folder_id)
            cfg.set_value("source_folder_name", folder_name)
            self._src_label.configure(text=f"📁  {folder_name}")
            self._refresh_file_count()

    def _refresh_file_count(self):
        ds = self.get_drive_service()
        if not ds:
            self._file_count_label.configure(text="")
            return

        def fetch():
            try:
                files = ds.list_files_in_folder(cfg.get("source_folder_id"))
                n = len(files)
                text = f"{n} file sẽ được copy" if n else "Thư mục này chưa có file"
                self.after(0, lambda: self._file_count_label.configure(text=text))
            except Exception:
                pass

        threading.Thread(target=fetch, daemon=True).start()

    def _select_duration(self, hours: int, label: str):
        self._duration_var.set(hours)
        for lbl, btn in self._dur_buttons.items():
            selected = lbl == label
            btn.configure(
                border_color=ACCENT if selected else BORDER,
                text_color=ACCENT if selected else SUBTEXT,
            )

    def _get_duration_hours(self) -> int | None:
        custom = self._custom_hours_var.get().strip()
        if custom:
            try:
                h = int(custom)
                return h if h > 0 else None
            except ValueError:
                return None
        return self._duration_var.get()

    # ──────────────────────────────────────────────────────────
    # Create flow
    # ──────────────────────────────────────────────────────────

    def _start_create(self):
        ds = self.get_drive_service()
        if not ds:
            self._show_error("Chưa đăng nhập Google. Vui lòng vào tab Cài đặt.")
            return

        hours = self._get_duration_hours()
        if not hours:
            self._show_error("Vui lòng chọn hoặc nhập thời hạn hợp lệ.")
            return

        folder_name = self._name_var.get().strip()
        if not folder_name:
            self._show_error("Vui lòng nhập tên thư mục.")
            return

        self._create_btn.configure(state="disabled", text="⏳  Đang xử lý...")
        self._show_progress()

        source_id = cfg.get("source_folder_id")
        expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=hours)

        def run():
            try:
                self._update_progress("📂  Đang tạo thư mục tạm...", 0.1)
                folder = ds.create_folder(folder_name)
                folder_id = folder["id"]

                self._update_progress("🔓  Đang bật chế độ share...", 0.25)
                ds.set_folder_public_share(folder_id)
                link = ds.get_folder_link(folder_id)

                self._update_progress("📋  Đang copy file...", 0.4)

                def on_progress(done, total):
                    pct = 0.4 + (done / max(total, 1)) * 0.45
                    self._update_progress(f"📋  Đang copy {done}/{total} file...", pct)

                ds.copy_files_from_folder(source_id, folder_id, on_progress)

                self._update_progress("🕐  Đang ghi lịch xóa tự động...", 0.9)
                ds.add_to_queue(folder_id, folder_name, expires_at)

                cfg.set_value("last_link", link)
                self.after(0, lambda: self._on_done(link, folder_id, folder_name, expires_at, hours))

            except Exception as e:
                self.after(0, lambda: self._show_error(f"Lỗi: {e}"))
                self.after(0, lambda: self._create_btn.configure(
                    state="normal", text="🚀  Tạo & Share ngay"
                ))

        threading.Thread(target=run, daemon=True).start()

    def _update_progress(self, msg: str, pct: float):
        self.after(0, lambda: self._progress_label.configure(text=msg))
        self.after(0, lambda: self._progressbar.set(pct))

    def _show_progress(self):
        self._progress_frame.pack(fill="x", padx=24, pady=(0, 24))
        self._progressbar.pack(fill="x", padx=16, pady=(4, 0))
        self._link_entry.pack_forget()
        self._copy_btn.pack_forget()

    def _on_done(self, link: str, folder_id: str, folder_name: str,
                 expires_at: datetime.datetime, hours: int):
        self._progressbar.set(1.0)
        self._progress_label.configure(
            text=f"✅  Hoàn tất! Link share đã sẵn sàng. Sẽ tự xóa sau {hours} giờ.",
            text_color=SUCCESS,
        )
        self._link_var.set(link)
        self._link_entry.pack(fill="x", padx=16, pady=(12, 4))
        self._copy_btn.pack(padx=16, pady=(4, 14), fill="x")
        self._create_btn.configure(state="normal", text="🚀  Tạo & Share ngay")
        self._name_var.set(self._default_name())

        if self.on_share_created:
            self.on_share_created()

    def _copy_link(self):
        self.clipboard_clear()
        self.clipboard_append(self._link_var.get())
        self._copy_btn.configure(text="✔  Đã copy!", fg_color="#3A8C60")
        self.after(2000, lambda: self._copy_btn.configure(text="📋  Copy Link", fg_color=SUCCESS))

    def _show_error(self, msg: str):
        self._progress_frame.pack(fill="x", padx=24, pady=(0, 24))
        self._progress_label.configure(text=f"❌  {msg}", text_color=ERROR)
        self._progressbar.pack_forget()
        self._link_entry.pack_forget()
        self._copy_btn.pack_forget()
