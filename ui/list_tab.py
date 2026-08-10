"""
List Tab — shows all active temp shared folders with countdowns.
"""
import threading
import datetime
import webbrowser
import customtkinter as ctk


ACCENT  = "#4F8EF7"
BG      = "#1A1D2E"
CARD    = "#242840"
CARD2   = "#1E2238"
TEXT    = "#E8EAF6"
SUBTEXT = "#9095B8"
SUCCESS = "#4CAF7D"
HOVER   = "#2E3255"
BORDER  = "#3A3F6B"
ERROR   = "#FF6B6B"
WARN    = "#F4A261"


class ListTab(ctk.CTkFrame):
    def __init__(self, parent, get_drive_service):
        super().__init__(parent, fg_color=BG)
        self.get_drive_service = get_drive_service
        self._rows = {}  # folder_id -> row widgets dict
        self._after_id = None
        self._build_ui()
        self.after(200, self.refresh)

    def _build_ui(self):
        # ── Header ──────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 8))

        ctk.CTkLabel(
            header, text="📋  Danh sách đang chia sẻ",
            font=("Inter", 20, "bold"), text_color=TEXT,
        ).pack(side="left")

        self._refresh_btn = ctk.CTkButton(
            header, text="🔄  Làm mới", width=100, height=32,
            fg_color=CARD, hover_color=HOVER,
            text_color=SUBTEXT, font=("Inter", 12),
            command=self.refresh,
        )
        self._refresh_btn.pack(side="right")

        self._status_label = ctk.CTkLabel(
            self, text="",
            font=("Inter", 11), text_color=SUBTEXT,
        )
        self._status_label.pack(anchor="e", padx=26, pady=(0, 8))

        # ── Scrollable list ─────────────────────────────────
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color=BG, scrollbar_button_color=CARD,
        )
        self._scroll.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self._empty_label = ctk.CTkLabel(
            self._scroll,
            text="🎉  Chưa có thư mục nào đang chia sẻ",
            font=("Inter", 14), text_color=SUBTEXT,
        )

    def refresh(self):
        """Reload the queue from Drive and re-render the list."""
        self._status_label.configure(text="⏳  Đang tải...")
        self._refresh_btn.configure(state="disabled")

        def fetch():
            ds = self.get_drive_service()
            if not ds:
                self.after(0, lambda: self._status_label.configure(
                    text="Chưa đăng nhập"
                ))
                self.after(0, lambda: self._refresh_btn.configure(state="normal"))
                return
            try:
                queue = ds.read_queue()
                self.after(0, lambda: self._render(queue, ds))
            except Exception as e:
                self.after(0, lambda: self._status_label.configure(
                    text=f"Lỗi: {e}"
                ))
                self.after(0, lambda: self._refresh_btn.configure(state="normal"))

        threading.Thread(target=fetch, daemon=True).start()

    def _render(self, queue: list[dict], ds):
        self._refresh_btn.configure(state="normal")
        now = datetime.datetime.now(datetime.timezone.utc)
        active = [
            e for e in queue
            if datetime.datetime.fromisoformat(e["expires_at"]) > now
        ]
        self._status_label.configure(
            text=f"Cập nhật lúc {datetime.datetime.now().strftime('%H:%M:%S')} — {len(active)} mục"
        )

        # Clear existing rows
        for w in self._scroll.winfo_children():
            w.destroy()
        self._rows = {}

        if not active:
            self._empty_label = ctk.CTkLabel(
                self._scroll,
                text="🎉  Chưa có thư mục nào đang chia sẻ",
                font=("Inter", 14), text_color=SUBTEXT,
            )
            self._empty_label.pack(pady=60)
            return

        for entry in active:
            self._add_row(entry, ds)

        # Start countdown ticker
        self._start_countdown()

    def _add_row(self, entry: dict, ds):
        folder_id = entry["folder_id"]
        expires_at = datetime.datetime.fromisoformat(entry["expires_at"])
        created_at = datetime.datetime.fromisoformat(entry["created_at"])

        card = ctk.CTkFrame(self._scroll, fg_color=CARD, corner_radius=12)
        card.pack(fill="x", padx=8, pady=6)

        # ── Row top: name + countdown ────────────────────
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(12, 4))

        ctk.CTkLabel(
            top, text=f"📁  {entry['folder_name']}",
            font=("Inter", 13, "bold"), text_color=TEXT, anchor="w",
        ).pack(side="left", fill="x", expand=True)

        countdown_label = ctk.CTkLabel(
            top, text="", font=("Inter", 12, "bold"),
            text_color=WARN, anchor="e",
        )
        countdown_label.pack(side="right")

        # ── Progress bar ─────────────────────────────────
        total_secs = (expires_at - created_at).total_seconds()
        prog_bar = ctk.CTkProgressBar(
            card, fg_color=CARD2, progress_color=WARN, height=4,
        )
        prog_bar.pack(fill="x", padx=14, pady=2)

        # ── Row bottom: created + buttons ─────────────────
        bottom = ctk.CTkFrame(card, fg_color="transparent")
        bottom.pack(fill="x", padx=14, pady=(4, 12))

        local_created = created_at.astimezone().strftime("%d/%m %H:%M")
        ctk.CTkLabel(
            bottom, text=f"Tạo lúc {local_created}",
            font=("Inter", 11), text_color=SUBTEXT, anchor="w",
        ).pack(side="left")

        # Open link button
        link = f"https://drive.google.com/drive/folders/{folder_id}"
        ctk.CTkButton(
            bottom, text="🔗  Mở link", width=88, height=28,
            fg_color="transparent", hover_color=HOVER,
            border_color=ACCENT, border_width=1,
            text_color=ACCENT, font=("Inter", 11),
            command=lambda u=link: webbrowser.open(u),
        ).pack(side="right", padx=(6, 0))

        # Copy link button
        ctk.CTkButton(
            bottom, text="📋  Copy", width=70, height=28,
            fg_color="transparent", hover_color=HOVER,
            border_color=BORDER, border_width=1,
            text_color=SUBTEXT, font=("Inter", 11),
            command=lambda u=link: self._copy(u),
        ).pack(side="right", padx=(6, 0))

        # Delete button
        del_btn = ctk.CTkButton(
            bottom, text="🗑  Xóa ngay", width=88, height=28,
            fg_color="transparent", hover_color="#4A1A1A",
            border_color=ERROR, border_width=1,
            text_color=ERROR, font=("Inter", 11),
            command=lambda fid=folder_id, c=card: self._delete_entry(fid, c, ds),
        )
        del_btn.pack(side="right", padx=(6, 0))

        self._rows[folder_id] = {
            "countdown": countdown_label,
            "progbar": prog_bar,
            "expires_at": expires_at,
            "created_at": created_at,
            "total_secs": total_secs,
        }

    def _start_countdown(self):
        if self._after_id:
            self.after_cancel(self._after_id)
        self._tick()

    def _tick(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        for fid, row in self._rows.items():
            remaining = (row["expires_at"] - now).total_seconds()
            if remaining <= 0:
                row["countdown"].configure(text="Hết hạn", text_color=ERROR)
                row["progbar"].set(0)
            else:
                h, rem = divmod(int(remaining), 3600)
                m, s = divmod(rem, 60)
                label = f"{h:02d}:{m:02d}:{s:02d}"
                color = ERROR if remaining < 3600 else WARN if remaining < 21600 else SUCCESS
                row["countdown"].configure(text=label, text_color=color)
                pct = max(0, remaining / max(row["total_secs"], 1))
                row["progbar"].set(pct)
                row["progbar"].configure(progress_color=color)
        self._after_id = self.after(1000, self._tick)

    def _delete_entry(self, folder_id: str, card: ctk.CTkFrame, ds):
        """Delete folder from Drive and remove from queue."""
        def run():
            try:
                if ds.folder_exists(folder_id):
                    ds.delete_folder(folder_id)
                ds.remove_from_queue(folder_id)
                self.after(0, lambda: card.destroy())
                self.after(0, lambda: self._rows.pop(folder_id, None))
            except Exception as e:
                self.after(0, lambda: self._show_error(str(e)))

        card.configure(fg_color="#2A1520")
        threading.Thread(target=run, daemon=True).start()

    def _copy(self, url: str):
        self.clipboard_clear()
        self.clipboard_append(url)

    def _show_error(self, msg: str):
        ctk.CTkLabel(
            self._scroll, text=f"❌  {msg}",
            font=("Inter", 12), text_color=ERROR,
        ).pack(pady=8)
