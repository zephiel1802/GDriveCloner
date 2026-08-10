"""
Settings Tab — Google account connection, default preferences.
"""
import os
import threading
import customtkinter as ctk
from auth import google_auth
from services import config as cfg


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

CREDS_PATH = os.path.join(os.path.dirname(__file__), "..", "credentials.json")


class SettingsTab(ctk.CTkFrame):
    def __init__(self, parent, on_auth_change):
        super().__init__(parent, fg_color=BG)
        self.on_auth_change = on_auth_change
        self._build_ui()
        self._check_auth_status()

    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color=BG, scrollbar_button_color=CARD)
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(
            scroll, text="⚙️  Cài đặt",
            font=("Inter", 20, "bold"), text_color=TEXT,
        ).pack(anchor="w", padx=28, pady=(24, 4))

        # ── Google Account ────────────────────────────────
        self._make_section(scroll, "🔐  Tài khoản Google")
        auth_card = ctk.CTkFrame(scroll, fg_color=CARD, corner_radius=12)
        auth_card.pack(fill="x", padx=24, pady=(4, 16))

        self._auth_status = ctk.CTkLabel(
            auth_card, text="⏳  Đang kiểm tra...",
            font=("Inter", 13), text_color=SUBTEXT, anchor="w",
        )
        self._auth_status.pack(anchor="w", padx=16, pady=(14, 6))

        self._user_label = ctk.CTkLabel(
            auth_card, text="",
            font=("Inter", 11), text_color=SUBTEXT, anchor="w",
        )
        self._user_label.pack(anchor="w", padx=16, pady=(0, 4))

        btn_row = ctk.CTkFrame(auth_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(4, 14))

        self._login_btn = ctk.CTkButton(
            btn_row, text="🔑  Đăng nhập Google",
            width=180, height=36,
            fg_color=ACCENT, hover_color="#3A70D4",
            text_color="white", font=("Inter", 13, "bold"),
            command=self._do_login,
        )
        self._login_btn.pack(side="left")

        self._logout_btn = ctk.CTkButton(
            btn_row, text="Đăng xuất", width=100, height=36,
            fg_color="transparent", hover_color=HOVER,
            border_color=ERROR, border_width=1,
            text_color=ERROR, font=("Inter", 12),
            command=self._do_logout,
        )
        self._logout_btn.pack(side="left", padx=8)

        # ── Credentials file ────────────────────────────
        self._make_section(scroll, "📄  File credentials.json")
        creds_card = ctk.CTkFrame(scroll, fg_color=CARD, corner_radius=12)
        creds_card.pack(fill="x", padx=24, pady=(4, 16))

        creds_path = os.path.abspath(CREDS_PATH)
        exists = os.path.exists(creds_path)
        status_text = f"✅  Tìm thấy: {creds_path}" if exists else f"❌  Chưa có file credentials.json"
        status_color = SUCCESS if exists else ERROR

        ctk.CTkLabel(
            creds_card, text=status_text,
            font=("Inter", 11), text_color=status_color,
            wraplength=440, anchor="w",
        ).pack(anchor="w", padx=16, pady=12)

        ctk.CTkLabel(
            creds_card,
            text="Tải credentials.json từ Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client IDs",
            font=("Inter", 11), text_color=SUBTEXT,
            wraplength=440, anchor="w",
        ).pack(anchor="w", padx=16, pady=(0, 12))

        # ── Default settings ─────────────────────────────
        self._make_section(scroll, "⚙️  Tuỳ chọn mặc định")
        pref_card = ctk.CTkFrame(scroll, fg_color=CARD, corner_radius=12)
        pref_card.pack(fill="x", padx=24, pady=(4, 16))

        # Default duration
        dur_row = ctk.CTkFrame(pref_card, fg_color="transparent")
        dur_row.pack(fill="x", padx=16, pady=(14, 6))
        ctk.CTkLabel(
            dur_row, text="Thời hạn mặc định (giờ):",
            font=("Inter", 12), text_color=TEXT, anchor="w",
        ).pack(side="left", fill="x", expand=True)
        self._dur_var = ctk.StringVar(value=str(cfg.get("default_duration_hours")))
        ctk.CTkEntry(
            dur_row, textvariable=self._dur_var,
            width=70, height=30,
            fg_color=CARD2, border_color=BORDER,
            text_color=TEXT, font=("Inter", 12),
        ).pack(side="right")

        # Folder prefix
        prefix_row = ctk.CTkFrame(pref_card, fg_color="transparent")
        prefix_row.pack(fill="x", padx=16, pady=(6, 6))
        ctk.CTkLabel(
            prefix_row, text="Tiền tố tên thư mục:",
            font=("Inter", 12), text_color=TEXT, anchor="w",
        ).pack(side="left", fill="x", expand=True)
        self._prefix_var = ctk.StringVar(value=cfg.get("temp_folder_prefix"))
        ctk.CTkEntry(
            prefix_row, textvariable=self._prefix_var,
            width=220, height=30,
            fg_color=CARD2, border_color=BORDER,
            text_color=TEXT, font=("Inter", 12),
        ).pack(side="right")

        ctk.CTkButton(
            pref_card, text="💾  Lưu cài đặt",
            height=36, font=("Inter", 13, "bold"),
            fg_color=ACCENT, hover_color="#3A70D4",
            text_color="white", corner_radius=8,
            command=self._save_prefs,
        ).pack(fill="x", padx=16, pady=(8, 14))

        self._save_label = ctk.CTkLabel(
            pref_card, text="",
            font=("Inter", 11), text_color=SUCCESS,
        )
        self._save_label.pack(pady=(0, 4))

        # ── Companion script instructions ─────────────────
        self._make_section(scroll, "🤖  Script tự động xóa (Apps Script)")
        info_card = ctk.CTkFrame(scroll, fg_color=CARD, corner_radius=12)
        info_card.pack(fill="x", padx=24, pady=(4, 24))

        instructions = (
            "Để thư mục tự xóa kể cả khi app đóng:\n\n"
            "1. Mở script.google.com → Tạo project mới\n"
            "2. Copy nội dung file AutoDelete.gs vào editor\n"
            "3. Bấm Run một lần để cấp quyền\n"
            "4. Vào Triggers (⏱) → Add Trigger:\n"
            "   • Function: autoDeleteExpiredFolders\n"
            "   • Event: Time-driven → Hour timer → Every hour\n"
            "5. Deploy xong là app tự xóa mỗi giờ!"
        )
        ctk.CTkLabel(
            info_card, text=instructions,
            font=("Inter", 11), text_color=SUBTEXT,
            wraplength=440, anchor="w", justify="left",
        ).pack(anchor="w", padx=16, pady=14)

    def _make_section(self, parent, text: str):
        ctk.CTkLabel(
            parent, text=text,
            font=("Inter", 12, "bold"), text_color=SUBTEXT,
        ).pack(anchor="w", padx=28, pady=(12, 2))

    def _check_auth_status(self):
        def check():
            ok = google_auth.is_authenticated()
            self.after(0, lambda: self._update_auth_ui(ok))

        threading.Thread(target=check, daemon=True).start()

    def _update_auth_ui(self, authenticated: bool):
        if authenticated:
            self._auth_status.configure(
                text="✅  Đã đăng nhập", text_color=SUCCESS
            )
            self._login_btn.configure(state="disabled")
            self._logout_btn.configure(state="normal")
        else:
            self._auth_status.configure(
                text="❌  Chưa đăng nhập", text_color=ERROR
            )
            self._login_btn.configure(state="normal")
            self._logout_btn.configure(state="disabled")
            self._user_label.configure(text="")

    def _do_login(self):
        self._login_btn.configure(state="disabled", text="⏳  Đang mở trình duyệt...")
        self._auth_status.configure(text="⏳  Đang xác thực...", text_color=SUBTEXT)

        def run():
            try:
                creds = google_auth.get_credentials()
                if creds:
                    user = google_auth.get_user_info(creds)
                    name = user.get("name", "")
                    email = user.get("email", "")
                    self.after(0, lambda: self._auth_status.configure(
                        text="✅  Đã đăng nhập thành công!", text_color=SUCCESS
                    ))
                    self.after(0, lambda: self._user_label.configure(
                        text=f"{name}  •  {email}"
                    ))
                    self.after(0, lambda: self._login_btn.configure(
                        state="disabled", text="🔑  Đăng nhập Google"
                    ))
                    self.after(0, lambda: self._logout_btn.configure(state="normal"))
                    if self.on_auth_change:
                        self.after(0, self.on_auth_change)
                else:
                    self.after(0, lambda: self._auth_status.configure(
                        text="❌  Đăng nhập thất bại. Kiểm tra credentials.json", text_color=ERROR
                    ))
                    self.after(0, lambda: self._login_btn.configure(
                        state="normal", text="🔑  Đăng nhập Google"
                    ))
            except Exception as e:
                self.after(0, lambda: self._auth_status.configure(
                    text=f"❌  Lỗi: {e}", text_color=ERROR
                ))
                self.after(0, lambda: self._login_btn.configure(
                    state="normal", text="🔑  Đăng nhập Google"
                ))

        threading.Thread(target=run, daemon=True).start()

    def _do_logout(self):
        google_auth.revoke_credentials()
        self._update_auth_ui(False)
        if self.on_auth_change:
            self.on_auth_change()

    def _save_prefs(self):
        try:
            dur = int(self._dur_var.get())
            cfg.set_value("default_duration_hours", dur)
        except ValueError:
            pass
        cfg.set_value("temp_folder_prefix", self._prefix_var.get())
        self._save_label.configure(text="✅  Đã lưu!")
        self.after(2500, lambda: self._save_label.configure(text=""))
