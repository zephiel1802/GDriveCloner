# 🗂️ GDriveCloner

> **Tạo thư mục chia sẻ tạm trên Google Drive — tự động xóa khi hết hạn.**  
> **Create temporary shared folders on Google Drive — auto-deleted when they expire.**  
> **在 Google Drive 上创建临时共享文件夹——过期后自动删除。**

GDriveCloner là desktop app Python thay thế hoàn toàn các Google Apps Script thủ công. Chỉ cần vài click là có link share sẵn sàng gửi cho người khác, và app tự xóa sau thời hạn bạn chọn — kể cả khi đóng app.

![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

<details open>
<summary>🇻🇳 Tiếng Việt</summary>

## ✨ Tính năng

| Tính năng | Mô tả |
|---|---|
| 📂 Folder Browser | Duyệt thư mục Google Drive trực tiếp trong app, không cần copy ID |
| 🚀 Tạo link share | Copy file → tạo folder tạm → bật public link → 1 click |
| ⏱ Hẹn giờ tự xóa | Chọn 1h / 6h / 12h / 24h hoặc nhập số giờ tuỳ ý |
| 🤖 Auto-delete | Tích hợp Apps Script trigger — tự xóa kể cả khi app đóng |
| 📋 Danh sách | Xem tất cả folder đang share, countdown thời gian còn lại |
| 🗑 Xóa thủ công | Xóa ngay bất kỳ folder nào từ tab Danh sách |
| 📥 Clone Drive | Copy toàn bộ thư mục Drive người khác về Drive của bạn |

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

### Tab 📥 Clone

Dùng để **sao chép toàn bộ thư mục Drive** mà người khác đã chia sẻ về Drive của bạn.

1. **Link nguồn**: Dán link Google Drive hoặc Folder ID vào ô input  
   _(ví dụ: `https://drive.google.com/drive/folders/ABC123...`)_
2. **Thư mục đích**: Click **"Duyệt"** để chọn thư mục trong Drive của bạn,  
   hoặc nhập tên vào ô **"Tên thư mục mới"** → Click **"＋ Tạo & chọn"** để tạo thư mục mới
3. Click **"🚀 Bắt đầu Clone"** → theo dõi tiến trình trong log real-time
4. Khi hoàn tất, xem thống kê: số file đã copy, bỏ qua, thư mục tạo mới, lỗi

> [!TIP]
> App tự động **bỏ qua file đã tồn tại** (theo tên) trong thư mục đích, tránh copy trùng lặp.

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
├── web/
│   ├── index.html              # Giao diện web app
│   ├── app.js                  # Logic frontend
│   └── style.css               # Stylesheet
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

</details>

---

<details>
<summary>🇬🇧 English</summary>

## ✨ Features

| Feature | Description |
|---|---|
| 📂 Folder Browser | Browse Google Drive folders directly in the app — no need to copy IDs |
| 🚀 Create Share Link | Copy files → create temp folder → enable public link → 1 click |
| ⏱ Auto-delete Timer | Choose 1h / 6h / 12h / 24h or enter any number of hours |
| 🤖 Auto-delete | Integrated Apps Script trigger — auto-deletes even when the app is closed |
| 📋 Active Shares List | View all shared folders with remaining time countdown |
| 🗑 Manual Delete | Delete any folder immediately from the List tab |
| 📥 Clone Drive | Copy an entire shared Drive folder to your own Drive |

---

## 🚀 Quick Setup

### macOS / Linux

```bash
# 1. Clone the repo
git clone https://github.com/zephiel1802/GDriveCloner.git
cd GDriveCloner

# 2. Add credentials.json (see guide below)

# 3. Run
chmod +x run.sh
./run.sh
```

`run.sh` will **automatically** check Python and install all dependencies.

### Windows

```bat
REM 1. Clone the repo
git clone https://github.com/zephiel1802/GDriveCloner.git
cd GDriveCloner

REM 2. Add credentials.json (see guide below)

REM 3. Double-click run.bat (or run as Administrator)
```

`run.bat` automatically **requests Admin privileges**, checks Python, and installs dependencies.

---

## 🔐 Google Credentials Setup (required — done once)

### Step 1 — Open Google Cloud Console

1. Go to **[console.cloud.google.com](https://console.cloud.google.com)**
2. Create a new project or select an existing one

### Step 2 — Enable Google Drive API

**APIs & Services → Library → "Google Drive API" → Enable**

### Step 3 — Create OAuth Credentials

1. **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client IDs**
2. Application type: **Desktop app**
3. Enter any name (e.g. `GDriveCloner`)
4. Click **Create** → **Download JSON**
5. Rename the downloaded file to **`credentials.json`**
6. Copy it to the project root (same folder as `main.py`)

> [!NOTE]
> `credentials.json` contains sensitive information. It is already added to `.gitignore` and should never be committed to GitHub.

### Step 4 — Run the app and log in

Run the app → browser opens automatically → sign in with Google → grant permissions → done!

---

## 🤖 Auto-delete Setup (required — done once)

To auto-delete folders **even when the app is closed**:

1. Go to **[script.google.com](https://script.google.com)** → **New project**
2. Clear the default code and paste the full contents of [`companion_script/AutoDelete.gs`](companion_script/AutoDelete.gs)
3. Click **▶ Run** once (to grant Drive permissions)
4. Go to **Triggers (⏱)** → **Add Trigger**:
   - **Function**: `autoDeleteExpiredFolders`
   - **Event source**: `Time-driven`
   - **Type**: `Hour timer` → `Every 1 hour`
5. **Save** → Done!

From now on, Apps Script will automatically check and delete expired folders every hour.

---

## 📖 User Guide

### ✨ Create Share Tab

1. **Source folder**: Click **"Change"** → browse Drive folders directly in the app (no folder ID needed)
2. **Temp folder name**: Auto-filled with date/time, editable as desired
3. **Duration**: Quick select 1h / 6h / 12h / 24h / 48h, or enter any number of hours
4. Click **"🚀 Create & Share Now"** → wait a few seconds → copy the link

### 📋 List Tab

- View all currently shared folders
- **Countdown** shows remaining time (changes color when nearly expired)
- **Visual progress bar**
- **"🗑 Delete Now"** button to manually delete any folder immediately
- **"🔗 Open Link"** button to open directly in the browser

### 📥 Clone Tab

Used to **copy an entire shared Drive folder** to your own Google Drive.

1. **Source link**: Paste a Google Drive link or Folder ID into the input field  
   _(e.g. `https://drive.google.com/drive/folders/ABC123...`)_
2. **Destination folder**: Click **"Browse"** to pick a folder in your Drive,  
   or type a name in the **"New folder name"** field → click **"＋ Create & select"** to create a new folder
3. Click **"🚀 Start Clone"** → monitor progress in the real-time log
4. When done, review the summary: files copied, skipped, folders created, errors

> [!TIP]
> The app automatically **skips files that already exist** (by name) in the destination folder to avoid duplicates.

### ⚙️ Settings Tab

- Sign in / sign out of Google account
- View `credentials.json` file status
- Set the **default duration** for the next share
- Set the **name prefix** for temporary folders
- Guide to deploy the companion Apps Script

---

## 📁 Project Structure

```
GDriveCloner/
├── main.py                     # Entry point
├── run.sh                      # macOS/Linux launcher (auto-install)
├── run.bat                     # Windows launcher (auto-install, admin)
├── requirements.txt            # Python dependencies
├── credentials.json            # ← Add this yourself (not committed)
│
├── auth/
│   └── google_auth.py          # OAuth2 flow & token management
│
├── services/
│   ├── drive_service.py        # Google Drive API wrapper
│   └── config.py               # Local config (JSON)
│
├── web/
│   ├── index.html              # Web UI
│   ├── app.js                  # Frontend logic
│   └── style.css               # Stylesheet
│
└── companion_script/
    └── AutoDelete.gs           # Apps Script — deploy once
```

---

## ⚙️ Manual Install (if not using run.sh / run.bat)

```bash
pip3 install -r requirements.txt
python3 main.py
```

### Requirements

- Python 3.9 or newer
- Internet connection (for Google authentication and Drive API)
- A Google account with Drive

---

## 🔒 Security

- `credentials.json` and `token.json` are in `.gitignore` — **never committed**
- Auth data is stored only on your machine
- The app only requests **Google Drive** permission (scope: `https://www.googleapis.com/auth/drive`)
- `_share_manager_queue.json` is stored in your Drive and readable only by you

</details>

---

<details>
<summary>🇨🇳 中文</summary>

## ✨ 功能特性

| 功能 | 说明 |
|---|---|
| 📂 文件夹浏览器 | 直接在应用内浏览 Google Drive 文件夹，无需复制 ID |
| 🚀 创建分享链接 | 复制文件 → 创建临时文件夹 → 开启公开链接 → 一键操作 |
| ⏱ 定时自动删除 | 选择 1h / 6h / 12h / 24h 或自定义小时数 |
| 🤖 自动删除 | 集成 Apps Script 触发器——即使应用关闭也能自动删除 |
| 📋 分享列表 | 查看所有正在分享的文件夹及剩余时间倒计时 |
| 🗑 手动删除 | 随时从列表标签页立即删除任意文件夹 |
| 📥 克隆 Drive | 将他人分享的整个 Drive 文件夹复制到您自己的 Drive |

---

## 🚀 快速安装

### macOS / Linux

```bash
# 1. 克隆仓库
git clone https://github.com/zephiel1802/GDriveCloner.git
cd GDriveCloner

# 2. 添加 credentials.json（见下方说明）

# 3. 运行
chmod +x run.sh
./run.sh
```

`run.sh` 将**自动**检测 Python 并安装所有依赖。

### Windows

```bat
REM 1. 克隆仓库
git clone https://github.com/zephiel1802/GDriveCloner.git
cd GDriveCloner

REM 2. 添加 credentials.json（见下方说明）

REM 3. 双击 run.bat（或以管理员身份运行）
```

`run.bat` 会自动**请求管理员权限**，检查 Python 并安装依赖。

---

## 🔐 配置 Google 凭据（必须——只需操作一次）

### 第一步 — 打开 Google Cloud Console

1. 访问 **[console.cloud.google.com](https://console.cloud.google.com)**
2. 创建新项目或选择现有项目

### 第二步 — 启用 Google Drive API

**APIs & Services → Library → "Google Drive API" → Enable**

### 第三步 — 创建 OAuth 凭据

1. **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client IDs**
2. 应用类型选择：**Desktop app**
3. 输入任意名称（例如 `GDriveCloner`）
4. 点击 **Create** → **Download JSON**
5. 将下载的文件重命名为 **`credentials.json`**
6. 复制到项目根目录（与 `main.py` 同级）

> [!NOTE]
> `credentials.json` 包含敏感信息。该文件已添加至 `.gitignore`，切勿提交到 GitHub。

### 第四步 — 运行应用并登录

运行应用 → 浏览器自动打开 → 使用 Google 账号登录 → 授予权限 → 完成！

---

## 🤖 配置自动删除（必须——只需操作一次）

若希望文件夹在**应用关闭时也能自动删除**：

1. 访问 **[script.google.com](https://script.google.com)** → **新建项目**
2. 清除默认代码，将 [`companion_script/AutoDelete.gs`](companion_script/AutoDelete.gs) 的全部内容粘贴进去
3. 点击 **▶ 运行** 一次（用于授权 Drive 权限）
4. 进入 **触发器 (⏱)** → **添加触发器**：
   - **函数**：`autoDeleteExpiredFolders`
   - **事件来源**：`时间驱动型`
   - **类型**：`小时计时器` → `每小时`
5. **保存** → 完成！

此后，Apps Script 将每小时自动检查并删除已到期的文件夹。

---

## 📖 使用说明

### ✨ 创建分享标签页

1. **源文件夹**：点击 **"更改"** → 直接在应用内浏览 Drive 文件夹（无需知道文件夹 ID）
2. **临时文件夹名称**：自动填入日期时间，可自行修改
3. **有效期**：快速选择 1h / 6h / 12h / 24h / 48h，或输入任意小时数
4. 点击 **"🚀 立即创建并分享"** → 等待几秒 → 复制链接

### 📋 列表标签页

- 查看所有正在分享的文件夹
- **倒计时**显示剩余时间（即将到期时颜色变化）
- **可视化进度条**
- **"🗑 立即删除"** 按钮可随时手动删除
- **"🔗 打开链接"** 按钮直接在浏览器中打开

### 📥 克隆标签页

用于将他人分享的 **整个 Drive 文件夹** 复制到您自己的 Google Drive。

1. **源链接**：将 Google Drive 链接或文件夹 ID 粘贴到输入框  
   _（例如：`https://drive.google.com/drive/folders/ABC123...`）_
2. **目标文件夹**：点击 **"浏览"** 选择您 Drive 中的文件夹，  
   或在 **"新建文件夹名称"** 输入框中输入名称 → 点击 **"＋ 创建并选择"** 新建文件夹
3. 点击 **"🚀 开始克隆"** → 在实时日志中查看进度
4. 完成后查看统计信息：已复制文件数、已跳过、新建文件夹数、错误数

> [!TIP]
> 应用会自动**跳过目标文件夹中已存在的同名文件**，避免重复复制。

### ⚙️ 设置标签页

- 登录 / 退出 Google 账号
- 查看 `credentials.json` 文件状态
- 设置下次创建分享的**默认有效期**
- 设置临时文件夹的**名称前缀**
- 查看 companion Apps Script 部署指南

---

## 📁 项目结构

```
GDriveCloner/
├── main.py                     # 入口文件
├── run.sh                      # macOS/Linux 启动脚本（自动安装）
├── run.bat                     # Windows 启动脚本（自动安装，需管理员）
├── requirements.txt            # Python 依赖
├── credentials.json            # ← 自行添加（不提交）
│
├── auth/
│   └── google_auth.py          # OAuth2 流程与令牌管理
│
├── services/
│   ├── drive_service.py        # Google Drive API 封装
│   └── config.py               # 本地配置（JSON）
│
├── web/
│   ├── index.html              # Web 界面
│   ├── app.js                  # 前端逻辑
│   └── style.css               # 样式表
│
└── companion_script/
    └── AutoDelete.gs           # Apps Script——部署一次即可
```

---

## ⚙️ 手动安装（不使用 run.sh / run.bat）

```bash
pip3 install -r requirements.txt
python3 main.py
```

### 系统要求

- Python 3.9 或更高版本
- 网络连接（用于 Google 身份验证和调用 Drive API）
- 拥有 Drive 的 Google 账号

---

## 🔒 安全性

- `credentials.json` 和 `token.json` 已加入 `.gitignore`——**永远不会被提交**
- 认证数据仅保存在您的本地机器上
- 应用仅申请 **Google Drive** 权限（scope：`https://www.googleapis.com/auth/drive`）
- `_share_manager_queue.json` 存储在您的 Drive 中，仅您本人可读

</details>

---

## 📄 License

MIT License — free to use and modify.

---

> Made with ❤️ by [zephiel1802](https://github.com/zephiel1802)
