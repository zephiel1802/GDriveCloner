"""
Folder Browser Dialog — lets user navigate Drive folders visually.
"""
import threading
import customtkinter as ctk


class FolderBrowserDialog(ctk.CTkToplevel):
    """
    A modal dialog that shows a navigable tree of Google Drive folders.
    Usage:
        dlg = FolderBrowserDialog(parent, drive_service)
        parent.wait_window(dlg)
        if dlg.result:
            folder_id, folder_name = dlg.result
    """

    ACCENT = "#4F8EF7"
    BG = "#1A1D2E"
    CARD = "#242840"
    TEXT = "#E8EAF6"
    SUBTEXT = "#9095B8"
    HOVER = "#2E3255"

    def __init__(self, parent, drive_service):
        super().__init__(parent)
        self.drive_service = drive_service
        self.result = None

        # Navigation stack: list of (folder_id, folder_name)
        self._nav_stack = [("root", "My Drive")]

        self.title("Chọn thư mục nguồn")
        self.geometry("520x480")
        self.resizable(False, False)
        self.configure(fg_color=self.BG)
        self.grab_set()
        self.focus()

        self._build_ui()
        self._load_folders()

    def _build_ui(self):
        # ── Header ──────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=self.CARD, corner_radius=0, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)

        self._back_btn = ctk.CTkButton(
            header, text="← Quay lại", width=90, height=32,
            fg_color="transparent", hover_color=self.HOVER,
            text_color=self.ACCENT, font=("Inter", 12),
            command=self._go_back,
        )
        self._back_btn.pack(side="left", padx=12, pady=12)

        self._path_label = ctk.CTkLabel(
            header, text="My Drive", font=("Inter", 13, "bold"),
            text_color=self.TEXT,
        )
        self._path_label.pack(side="left", padx=4)

        # ── Search ─────────────────────────────────────────
        search_frame = ctk.CTkFrame(self, fg_color=self.CARD, corner_radius=0, height=44)
        search_frame.pack(fill="x")
        search_frame.pack_propagate(False)

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", self._on_search)
        search_entry = ctk.CTkEntry(
            search_frame, textvariable=self._search_var,
            placeholder_text="🔍  Tìm thư mục...",
            fg_color=self.BG, border_color="#3A3F6B",
            text_color=self.TEXT, height=30,
        )
        search_entry.pack(fill="x", padx=12, pady=7)

        # ── Folder list ─────────────────────────────────────
        self._list_frame = ctk.CTkScrollableFrame(
            self, fg_color=self.BG, scrollbar_button_color=self.CARD,
        )
        self._list_frame.pack(fill="both", expand=True, padx=0, pady=0)

        self._loading_label = ctk.CTkLabel(
            self._list_frame, text="⏳  Đang tải...",
            font=("Inter", 13), text_color=self.SUBTEXT,
        )
        self._loading_label.pack(pady=40)

        # ── Footer ──────────────────────────────────────────
        footer = ctk.CTkFrame(self, fg_color=self.CARD, corner_radius=0, height=56)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        self._select_btn = ctk.CTkButton(
            footer, text="✔  Chọn thư mục này",
            fg_color=self.ACCENT, hover_color="#3A70D4",
            text_color="white", font=("Inter", 13, "bold"),
            height=36, width=200,
            command=self._select_current,
        )
        self._select_btn.pack(side="right", padx=16, pady=10)

        ctk.CTkButton(
            footer, text="Huỷ", width=80, height=36,
            fg_color="transparent", hover_color=self.HOVER,
            text_color=self.SUBTEXT, font=("Inter", 13),
            command=self.destroy,
        ).pack(side="right", padx=4, pady=10)

        self._all_folders = []

    def _load_folders(self):
        """Load folders for the current nav stack level in a background thread."""
        self._clear_list()
        self._loading_label = ctk.CTkLabel(
            self._list_frame, text="⏳  Đang tải...",
            font=("Inter", 13), text_color=self.SUBTEXT,
        )
        self._loading_label.pack(pady=40)

        current_id = self._nav_stack[-1][0]
        self._back_btn.configure(state="normal" if len(self._nav_stack) > 1 else "disabled")
        self._path_label.configure(text=" › ".join(n for _, n in self._nav_stack))

        def fetch():
            try:
                folders = self.drive_service.list_folders(current_id)
                self.after(0, lambda: self._render_folders(folders))
            except Exception as e:
                self.after(0, lambda: self._show_error(str(e)))

        threading.Thread(target=fetch, daemon=True).start()

    def _render_folders(self, folders: list[dict]):
        self._all_folders = folders
        self._clear_list()
        self._draw_folder_rows(folders)

    def _draw_folder_rows(self, folders: list[dict]):
        if not folders:
            ctk.CTkLabel(
                self._list_frame, text="📂  Không có thư mục con",
                font=("Inter", 12), text_color=self.SUBTEXT,
            ).pack(pady=30)
            return

        for f in folders:
            row = ctk.CTkFrame(
                self._list_frame, fg_color="transparent",
                corner_radius=8, height=44,
            )
            row.pack(fill="x", padx=10, pady=2)
            row.pack_propagate(False)

            # Icon + name
            label = ctk.CTkLabel(
                row, text=f"📁  {f['name']}",
                font=("Inter", 13), text_color=self.TEXT,
                anchor="w",
            )
            label.pack(side="left", padx=12, fill="x", expand=True)

            # Open subfolder button
            open_btn = ctk.CTkButton(
                row, text="▶", width=30, height=28,
                fg_color="transparent", hover_color=self.HOVER,
                text_color=self.SUBTEXT, font=("Inter", 11),
                command=lambda fid=f["id"], fn=f["name"]: self._navigate_into(fid, fn),
            )
            open_btn.pack(side="right", padx=4)

            # Hover highlight
            for widget in (row, label):
                widget.bind("<Enter>", lambda e, r=row: r.configure(fg_color=self.HOVER))
                widget.bind("<Leave>", lambda e, r=row: r.configure(fg_color="transparent"))
                widget.bind(
                    "<Button-1>",
                    lambda e, fid=f["id"], fn=f["name"]: self._select_folder(fid, fn),
                )

    def _clear_list(self):
        for widget in self._list_frame.winfo_children():
            widget.destroy()

    def _navigate_into(self, folder_id: str, folder_name: str):
        self._nav_stack.append((folder_id, folder_name))
        self._search_var.set("")
        self._load_folders()

    def _go_back(self):
        if len(self._nav_stack) > 1:
            self._nav_stack.pop()
            self._search_var.set("")
            self._load_folders()

    def _select_folder(self, folder_id: str, folder_name: str):
        self.result = (folder_id, folder_name)
        self.destroy()

    def _select_current(self):
        current_id, current_name = self._nav_stack[-1]
        self.result = (current_id, current_name)
        self.destroy()

    def _on_search(self, *args):
        query = self._search_var.get().strip().lower()
        if not query:
            self._clear_list()
            self._draw_folder_rows(self._all_folders)
        else:
            filtered = [f for f in self._all_folders if query in f["name"].lower()]
            self._clear_list()
            self._draw_folder_rows(filtered)

    def _show_error(self, msg: str):
        self._clear_list()
        ctk.CTkLabel(
            self._list_frame, text=f"❌  Lỗi: {msg}",
            font=("Inter", 12), text_color="#FF6B6B",
        ).pack(pady=30)
