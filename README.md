# 🗂️ GDriveCloner

> **Tạo thư mục chia sẻ tạm trên Google Drive — tự động xóa khi hết hạn.**

GDriveCloner là desktop app Python thay thế hoàn toàn các Google Apps Script thủ công. Chỉ cần vài click là có link share sẵn sàng gửi cho người khác, và app tự xóa sau thời hạn bạn chọn — kể cả khi đóng app.

![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Tính năng

| Tính năng | Mô tả |
|---|---|
| 📂 Folder Browser | Duyệt thư mục Google Drive trực tiếp trong app, không cần copy ID |
| 🚀 Tạo link share | Copy file → tạo folder tạm → bật public link → 1 click |
| ⏱ Hẹn giờ tự xóa | Chọn 1h / 6h / 12h / 24h hoặc nhập số giờ tuỳ ý |
| 🤖 Auto-delete | Tích hợp Apps Script trigger — tự xóa kể cả khi app đóng |
| 📋 Danh sách | Xem tất cả folder đang share, countdown thời gian còn lại |
| 🗑 Xóa thủ công | Xóa ngay bất kỳ folder nào từ tab Danh sách |

---

## 🚀 Cài đặt nhanh

### macOS / Linux

```bash
# 1. Clone repo
git clone https://github.com/zephiel1802/GDriveCloner.git
cd GDriveCloner

# 2. Thêm credentials.json (xem hướng dẫn bên dưới)

# 3. Chạy
chmod +x run.sh
./run.sh
```

Script `run.sh` sẽ **tự động** kiểm tra Python và cài đặt tất cả dependencies.

### Windows

```bat
REM 1. Clone repo
git clone https://github.com/zephiel1802/GDriveCloner.git
cd GDriveCloner

REM 2. Thêm credentials.json (xem hướng dẫn bên dưới)

REM 3. Click đúp vào run.bat (hoặc chạy với quyền Admin)
```

Script `run.bat` tự động **yêu cầu quyền Admin**, kiểm tra Python và cài dependencies.

---

## 🔐 Thiết lập Google Credentials (bắt buộc — làm 1 lần)

### Bước 1 — Vào Google Cloud Console

1. Truy cập **[console.cloud.google.com](https://console.cloud.google.com)**
2. Tạo project mới hoặc chọn project có sẵn

### Bước 2 — Bật Google Drive API

**APIs & Services → Library → "Google Drive API" → Enable**

### Bước 3 — Tạo OAuth Credentials

1. **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client IDs**
2. Application type: **Desktop app**
3. Đặt tên tuỳ ý (ví dụ: `GDriveCloner`)
4. Click **Create** → **Download JSON**
5. Đổi tên file tải về thành **`credentials.json`**
6. Copy vào thư mục gốc của project (cùng chỗ với `main.py`)

> [!NOTE]
> File `credentials.json` chứa thông tin nhạy cảm. File này đã được thêm vào `.gitignore`, không bao giờ được commit lên GitHub.

### Bước 4 — Chạy app và đăng nhập

Chạy app lần đầu → trình duyệt tự mở → đăng nhập Google → cấp quyền → xong!

---

## 🤖 Thiết lập tự động xóa (bắt buộc — làm 1 lần)

Để folder tự xóa **kể cả khi app đóng**:

1. Vào **[script.google.com](https://script.google.com)** → **Dự án mới**
2. Xóa code mặc định, paste toàn bộ nội dung file [`companion_script/AutoDelete.gs`](companion_script/AutoDelete.gs)
3. Click **▶ Run** lần đầu (để cấp quyền Drive)
4. Vào **Triggers (⏱)** → **Add Trigger**:
   - **Function**: `autoDeleteExpiredFolders`
   - **Event source**: `Time-driven`
   - **Type**: `Hour timer` → `Every 1 hour`
5. **Save** → Xong!

Từ giờ, mỗi giờ Apps Script sẽ tự kiểm tra và xóa các folder đã hết hạn.

---

## 📖 Hướng dẫn sử dụng

### Tab ✨ Tạo Share

![Create Tab Flow](https://img.shields.io/badge/1.%20Chọn%20thư%20mục%20nguồn-blue) → ![](https://img.shields.io/badge/2.%20Đặt%20tên-blue) → ![](https://img.shields.io/badge/3.%20Chọn%20thời%20hạn-blue) → ![](https://img.shields.io/badge/4.%20Tạo%20%26%20Copy%20link-green)

1. **Thư mục nguồn**: Click **"Thay đổi"** → duyệt folder Drive ngay trong app (không cần biết folder ID)
2. **Tên thư mục tạm**: Tự động điền ngày giờ, có thể sửa tuỳ ý
3. **Thời hạn**: Chọn nhanh 1h / 6h / 12h / 24h / 48h, hoặc nhập số giờ bất kỳ
4. Click **"🚀 Tạo & Share ngay"** → đợi vài giây → copy link

### Tab 📋 Danh sách

- Xem tất cả folder đang được share
- **Countdown** hiển thị thời gian còn lại (đổi màu khi gần hết)
- **Thanh progress** trực quan
- Nút **"🗑 Xóa ngay"** để xóa thủ công bất cứ lúc nào
- Nút **"🔗 Mở link"** để mở thẳng trong browser

### Tab ⚙️ Cài đặt

- Đăng nhập / đăng xuất tài khoản Google
- Xem trạng thái file `credentials.json`
- Đặt **thời hạn mặc định** cho lần tạo tiếp theo
- Đặt **tiền tố tên** thư mục tạm
- Hướng dẫn deploy companion Apps Script

---

## 📁 Cấu trúc project

```
GDriveCloner/
├── main.py                     # Entry point — chạy app từ đây
├── run.sh                      # Launcher macOS/Linux (auto-install)
├── run.bat                     # Launcher Windows (auto-install, admin)
├── requirements.txt            # Python dependencies
├── credentials.json            # ← Bạn tự thêm (không commit)
│
├── auth/
│   └── google_auth.py          # OAuth2 flow & token management
│
├── services/
│   ├── drive_service.py        # Google Drive API wrapper
│   └── config.py               # Local config (JSON)
│
├── ui/
│   ├── app.py                  # Main window & sidebar navigation
│   ├── create_tab.py           # Tab tạo share
│   ├── list_tab.py             # Tab danh sách + countdown
│   ├── settings_tab.py         # Tab cài đặt
│   └── folder_browser.py       # Folder picker dialog
│
└── companion_script/
    └── AutoDelete.gs           # Apps Script — deploy 1 lần
```

---

## ⚙️ Cài thủ công (nếu không dùng run.sh / run.bat)

```bash
pip3 install -r requirements.txt
python3 main.py
```

### Yêu cầu

- Python 3.9 hoặc mới hơn
- Kết nối internet (để xác thực Google và gọi Drive API)
- Tài khoản Google với Drive

---

## 🔒 Bảo mật

- `credentials.json` và `token.json` được thêm vào `.gitignore` — **không bao giờ bị commit**
- Dữ liệu xác thực chỉ lưu trên máy bạn
- App chỉ yêu cầu quyền **Google Drive** (scope: `https://www.googleapis.com/auth/drive`)
- File `_share_manager_queue.json` được lưu trên Drive của bạn, chỉ bạn mới đọc được

---

## 📄 License

MIT License — free to use and modify.

---

> Made with ❤️ by [zephiel1802](https://github.com/zephiel1802)
