"""
Main Application Window — Drive Share Manager
"""
import customtkinter as ctk
from auth import google_auth
from services.drive_service import DriveService
from ui.create_tab import CreateTab
from ui.list_tab import ListTab
from ui.settings_tab import SettingsTab


ACCENT  = "#4F8EF7"
BG      = "#1A1D2E"
SIDEBAR = "#13162A"
CARD    = "#242840"
TEXT    = "#E8EAF6"
SUBTEXT = "#9095B8"
SELECTED_TAB = "#242840"


NAV_ITEMS = [
    ("✨", "Tạo Share", 0),
    ("📋", "Danh sách", 1),
    ("⚙️", "Cài đặt", 2),
]


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Drive Share Manager")
        self.geometry("860x620")
        self.minsize(760, 540)
        self.configure(fg_color=BG)

        self._drive_service: DriveService | None = None
        self._current_tab = 0

        self._build_layout()
        self._switch_tab(0)
        self._try_init_drive()

    # ──────────────────────────────────────────────
    # Layout
    # ──────────────────────────────────────────────

    def _build_layout(self):
        # ── Sidebar ──────────────────────────────────────
        self._sidebar = ctk.CTkFrame(
            self, width=200, fg_color=SIDEBAR, corner_radius=0,
        )
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        # Logo / title
        logo_frame = ctk.CTkFrame(self._sidebar, fg_color="transparent", height=72)
        logo_frame.pack(fill="x")
        logo_frame.pack_propagate(False)

        ctk.CTkLabel(
            logo_frame,
            text="🗂️",
            font=("Inter", 26),
        ).pack(side="left", padx=(16, 4), pady=20)
        ctk.CTkLabel(
            logo_frame,
            text="Share\nManager",
            font=("Inter", 13, "bold"),
            text_color=TEXT,
            justify="left",
        ).pack(side="left", pady=20)

        # Divider
        ctk.CTkFrame(self._sidebar, height=1, fg_color=CARD).pack(fill="x", padx=12, pady=4)

        # Nav buttons
        self._nav_buttons = []
        for icon, label, idx in NAV_ITEMS:
            btn = ctk.CTkButton(
                self._sidebar,
                text=f"  {icon}  {label}",
                anchor="w",
                height=44,
                fg_color="transparent",
                hover_color=CARD,
                text_color=SUBTEXT,
                font=("Inter", 13),
                corner_radius=8,
                command=lambda i=idx: self._switch_tab(i),
            )
            btn.pack(fill="x", padx=10, pady=3)
            self._nav_buttons.append(btn)

        # Bottom: auth status badge
        ctk.CTkFrame(self._sidebar, fg_color="transparent").pack(fill="both", expand=True)
        self._auth_badge = ctk.CTkLabel(
            self._sidebar, text="● Chưa đăng nhập",
            font=("Inter", 11), text_color="#FF6B6B", anchor="w",
        )
        self._auth_badge.pack(anchor="w", padx=16, pady=(0, 20))

        # ── Content area ─────────────────────────────────
        self._content = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self._content.pack(side="right", fill="both", expand=True)

        # Build tab frames (lazy: build on first visit)
        self._tabs: list[ctk.CTkFrame | None] = [None, None, None]

    # ──────────────────────────────────────────────
    # Tab switching
    # ──────────────────────────────────────────────

    def _switch_tab(self, idx: int):
        self._current_tab = idx

        # Update nav button styles
        for i, btn in enumerate(self._nav_buttons):
            if i == idx:
                btn.configure(fg_color=SELECTED_TAB, text_color=TEXT)
            else:
                btn.configure(fg_color="transparent", text_color=SUBTEXT)

        # Hide all tabs
        for tab in self._tabs:
            if tab:
                tab.pack_forget()

        # Build tab if not yet created
        if self._tabs[idx] is None:
            self._tabs[idx] = self._build_tab(idx)

        self._tabs[idx].pack(fill="both", expand=True)

        # Refresh list when switching to it
        if idx == 1 and isinstance(self._tabs[1], ListTab):
            self._tabs[1].refresh()

    def _build_tab(self, idx: int) -> ctk.CTkFrame:
        if idx == 0:
            return CreateTab(
                self._content,
                get_drive_service=self._get_drive_service,
                on_share_created=self._on_share_created,
            )
        elif idx == 1:
            return ListTab(
                self._content,
                get_drive_service=self._get_drive_service,
            )
        else:
            return SettingsTab(
                self._content,
                on_auth_change=self._on_auth_change,
            )

    # ──────────────────────────────────────────────
    # Drive service
    # ──────────────────────────────────────────────

    def _get_drive_service(self) -> DriveService | None:
        return self._drive_service

    def _try_init_drive(self):
        """Try to initialise the Drive service from cached credentials."""
        import threading

        def init():
            try:
                creds = google_auth.get_credentials()
                if creds:
                    self._drive_service = DriveService(creds)
                    self.after(0, lambda: self._auth_badge.configure(
                        text="● Đã kết nối", text_color="#4CAF7D"
                    ))
                    # Refresh list tab if already built
                    if isinstance(self._tabs[1], ListTab):
                        self.after(200, self._tabs[1].refresh)
            except Exception:
                pass

        threading.Thread(target=init, daemon=True).start()

    def _on_auth_change(self):
        """Called when user logs in or out in settings tab."""
        self._drive_service = None
        self._auth_badge.configure(text="● Đang kết nối...", text_color=SUBTEXT)
        self._try_init_drive()

    def _on_share_created(self):
        """Called when a new share is successfully created."""
        # Rebuild list tab so next visit shows fresh data
        if self._tabs[1]:
            self._tabs[1].pack_forget()
            self._tabs[1].destroy()
            self._tabs[1] = None
