"""
Flask API Server — Drive Share Manager
"""
import threading
import datetime
import json
import os
import sys
import shutil
import queue as q_module
import re as _re
import uuid as _uuid
from typing import Optional


def resource_path(relative_path: str) -> str:
    """
    Get the absolute path to a bundled resource.
    Works for:
      - Normal Python execution (returns path relative to this file's parent)
      - PyInstaller onefile bundle (uses sys._MEIPASS temp extraction dir)
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running inside PyInstaller bundle
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        # Running as normal Python script
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)


sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, jsonify, request, send_from_directory, Response
from auth import google_auth
from services.drive_service import DriveService
from services import config as cfg

app = Flask(__name__)

# ─── Global State ────────────────────────────────────────────────────────────
_drive_service: Optional[DriveService] = None
_drive_lock = threading.Lock()
_login_state: dict = {'status': 'idle', 'error': None}  # idle|running|done|error


def _get_ds() -> Optional[DriveService]:
    with _drive_lock:
        return _drive_service


def _set_ds(ds: Optional[DriveService]):
    global _drive_service
    with _drive_lock:
        _drive_service = ds


def _startup_init():
    """Load cached credentials on startup, then clean up expired share folders."""
    if not google_auth.is_authenticated():
        return
    try:
        creds = google_auth.get_credentials()
        if not creds:
            return
        ds = DriveService(creds)
        _set_ds(ds)
    except Exception:
        return

    # ── Startup cleanup: delete expired share folders ──────────────────────────
    try:
        now = datetime.datetime.now(datetime.timezone.utc)
        queue = ds.read_queue()
        remaining = []
        for entry in queue:
            try:
                exp = datetime.datetime.fromisoformat(entry['expires_at'])
                # Make offset-aware if needed
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=datetime.timezone.utc)
            except Exception:
                remaining.append(entry)
                continue

            if now >= exp:
                folder_id   = entry.get('folder_id', '')
                folder_name = entry.get('folder_name', folder_id)
                try:
                    if ds.folder_exists(folder_id):
                        ds.delete_folder(folder_id)
                        print(f'[startup cleanup] 🗑️  Đã xóa thư mục hết hạn: {folder_name}')
                    else:
                        print(f'[startup cleanup] ⚠️  Thư mục không còn tồn tại: {folder_name}')
                except Exception as exc:
                    print(f'[startup cleanup] ❌ Lỗi khi xóa {folder_name}: {exc}')
                    remaining.append(entry)   # keep in queue, retry next time
            else:
                remaining.append(entry)

        if len(remaining) != len(queue):
            ds.write_queue(remaining)
            print(f'[startup cleanup] ✅ Xóa {len(queue) - len(remaining)} thư mục hết hạn.')
        else:
            print('[startup cleanup] ✅ Không có thư mục hết hạn.')
    except Exception as exc:
        print(f'[startup cleanup] ❌ Lỗi khi đọc queue: {exc}')


threading.Thread(target=_startup_init, daemon=True).start()

# ─── Static Files ─────────────────────────────────────────────────────────────
WEB_DIR = resource_path('web')


@app.route('/')
def index():
    return send_from_directory(WEB_DIR, 'index.html')


@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(WEB_DIR, filename)


# ─── Auth API ─────────────────────────────────────────────────────────────────
@app.route('/api/status')
def api_status():
    ds = _get_ds()
    authenticated = ds is not None
    if not authenticated:
        authenticated = google_auth.is_authenticated()
        if authenticated:
            # Lazy-init drive service if token is valid but service not built yet
            try:
                creds = google_auth.get_credentials()
                if creds:
                    _set_ds(DriveService(creds))
            except Exception:
                pass
    return jsonify({
        'authenticated': authenticated,
        'login_state': _login_state['status'],
        'login_error': _login_state.get('error'),
    })


@app.route('/api/userinfo')
def api_userinfo():
    ds = _get_ds()
    if not ds:
        return jsonify({'authenticated': False})
    try:
        creds = google_auth.get_credentials()
        if creds:
            info = google_auth.get_user_info(creds)
            return jsonify({'authenticated': True, **info})
    except Exception:
        pass
    return jsonify({'authenticated': True})


@app.route('/api/creds-status')
def api_creds_status():
    creds_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'credentials.json'))
    return jsonify({'exists': os.path.exists(creds_path), 'path': creds_path})


@app.route('/api/upload-credentials', methods=['POST'])
def api_upload_credentials():
    """Accept a credentials.json file upload and save it to the app directory."""
    if 'file' not in request.files:
        return jsonify({'ok': False, 'error': 'No file uploaded'}), 400

    f = request.files['file']
    if not f or f.filename == '':
        return jsonify({'ok': False, 'error': 'No file selected'}), 400

    # Basic validation: must be valid JSON with expected keys
    try:
        content = f.read()
        data = json.loads(content)
        # Must contain 'installed' or 'web' top-level key (OAuth2 client secret format)
        if 'installed' not in data and 'web' not in data:
            return jsonify({'ok': False, 'error': 'File không hợp lệ. Cần file OAuth 2.0 Client ID từ Google Cloud Console.'}), 400
    except (json.JSONDecodeError, UnicodeDecodeError):
        return jsonify({'ok': False, 'error': 'File không phải JSON hợp lệ.'}), 400

    dest_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'credentials.json'))
    try:
        with open(dest_path, 'wb') as out:
            out.write(content)
        return jsonify({'ok': True, 'path': dest_path})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/auth/login', methods=['POST'])
def api_login():
    global _login_state
    if _login_state['status'] == 'running':
        return jsonify({'ok': True, 'status': 'running'})

    _login_state = {'status': 'running', 'error': None}

    def run():
        global _login_state
        try:
            creds = google_auth.get_credentials()
            if creds:
                _set_ds(DriveService(creds))
                _login_state = {'status': 'done', 'error': None}
            else:
                _login_state = {
                    'status': 'error',
                    'error': 'Đăng nhập thất bại. Kiểm tra credentials.json'
                }
        except Exception as e:
            _login_state = {'status': 'error', 'error': str(e)}

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'ok': True, 'status': 'running'})


@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    global _login_state
    google_auth.revoke_credentials()
    _set_ds(None)
    _login_state = {'status': 'idle', 'error': None}
    return jsonify({'ok': True})


# ─── Config API ───────────────────────────────────────────────────────────────
@app.route('/api/config', methods=['GET'])
def api_get_config():
    return jsonify(cfg.load())


@app.route('/api/config', methods=['POST'])
def api_set_config():
    data = request.get_json() or {}
    for k, v in data.items():
        cfg.set_value(k, v)
    return jsonify({'ok': True})


@app.route('/api/app/quit', methods=['POST'])
def api_app_quit():
    # Attempt to gracefully stop the Flask server
    import os
    import threading
    import time
    
    def shutdown():
        time.sleep(0.5)
        os._exit(0)
        
    threading.Thread(target=shutdown, daemon=True).start()
    return jsonify({'ok': True, 'msg': 'Shutting down'})


# ─── Queue API ────────────────────────────────────────────────────────────────
@app.route('/api/queue')
def api_queue():
    ds = _get_ds()
    if not ds:
        return jsonify({'error': 'Not authenticated'}), 401
    try:
        queue_data = ds.read_queue()
        now = datetime.datetime.now(datetime.timezone.utc)
        active = [
            e for e in queue_data
            if datetime.datetime.fromisoformat(e['expires_at']) > now
        ]
        return jsonify(active)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─── Share API ────────────────────────────────────────────────────────────────
@app.route('/api/share/create', methods=['POST'])
def api_create_share():
    ds = _get_ds()
    if not ds:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.get_json() or {}
    folder_name = (data.get('folder_name') or '').strip()
    hours = int(data.get('hours') or 24)
    source_id = data.get('source_folder_id') or cfg.get('source_folder_id') or 'root'

    if not folder_name:
        return jsonify({'error': 'Folder name is required'}), 400

    progress_q: q_module.Queue = q_module.Queue()

    def run():
        try:
            progress_q.put({'type': 'progress', 'msg': '📂 Đang tạo thư mục tạm...', 'pct': 0.1, 'step': 0})
            folder = ds.create_folder(folder_name)
            folder_id = folder['id']

            progress_q.put({'type': 'progress', 'msg': '🔓 Đang bật chế độ share...', 'pct': 0.25, 'step': 1})
            ds.set_folder_public_share(folder_id)
            link = ds.get_folder_link(folder_id)

            progress_q.put({'type': 'progress', 'msg': '📋 Đang quét và copy toàn bộ (bao gồm thư mục con)...', 'pct': 0.4, 'step': 2})

            def on_log(msg):
                text = msg if isinstance(msg, str) else msg.get('msg', '')
                progress_q.put({'type': 'progress', 'msg': text, 'pct': 0.5, 'step': 2})

            stats = ds.clone_folder_recursive(source_id, folder_id, on_log)

            expires_at = (
                datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(hours=hours)
            )
            progress_q.put({'type': 'progress', 'msg': '🕐 Đang ghi lịch xóa...', 'pct': 0.9, 'step': 3})
            ds.add_to_queue(folder_id, folder_name, expires_at)
            cfg.set_value('last_link', link)

            progress_q.put({
                'type': 'done',
                'link': link,
                'folder_id': folder_id,
                'folder_name': folder_name,
                'expires_at': expires_at.isoformat(),
                'hours': hours,
                'stats': stats,
            })
        except Exception as e:
            progress_q.put({'type': 'error', 'msg': str(e)})

    threading.Thread(target=run, daemon=True).start()

    def generate():
        while True:
            try:
                item = progress_q.get(timeout=120)
                yield 'data: ' + json.dumps(item, ensure_ascii=False) + '\n\n'
                if item['type'] in ('done', 'error'):
                    break
            except q_module.Empty:
                yield 'data: {"type":"ping"}\n\n'

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        },
    )


@app.route('/api/share/<folder_id>', methods=['DELETE'])
def api_delete_share(folder_id):
    ds = _get_ds()
    if not ds:
        return jsonify({'error': 'Not authenticated'}), 401
    try:
        if ds.folder_exists(folder_id):
            ds.delete_folder(folder_id)
        ds.remove_from_queue(folder_id)
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─── Folder Browser API ───────────────────────────────────────────────────────
@app.route('/api/folders')
def api_list_folders():
    ds = _get_ds()
    if not ds:
        return jsonify({'error': 'Not authenticated'}), 401
    parent_id = request.args.get('parent', 'root')
    try:
        folders = ds.list_folders(parent_id)
        return jsonify(folders)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/folders', methods=['POST'])
def api_create_folder():
    """Create a new folder and return its metadata."""
    ds = _get_ds()
    if not ds:
        return jsonify({'error': 'Not authenticated'}), 401
    data = request.get_json() or {}
    name      = (data.get('name') or '').strip()
    parent_id = (data.get('parent_id') or 'root').strip()
    if not name:
        return jsonify({'error': 'name is required'}), 400
    try:
        folder = ds.create_folder(name, parent_id)
        return jsonify({'ok': True, 'folder': folder})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─── Clone API ────────────────────────────────────────────────────────────────
# job_id -> { 'queue': Queue, 'status': 'running'|'done'|'error', 'log': [events] }
# Jobs survive SSE disconnects — browser can reconnect and replay history.
_clone_jobs: dict = {}
_clone_jobs_lock = threading.Lock()

SSE_PING_INTERVAL = 15   # seconds between keepalive pings (keeps proxies alive)


def _parse_drive_folder_id(raw: str) -> str:
    """
    Accept multiple input formats and return the bare folder ID:
      - https://drive.google.com/drive/folders/<id>
      - https://drive.google.com/drive/u/0/folders/<id>
      - https://drive.google.com/drive/u/0/folders/<id>?usp=sharing
      - bare ID (any alphanumeric string)
    """
    raw = raw.strip()
    match = _re.search(r'/folders/([a-zA-Z0-9_-]{10,})', raw)
    if match:
        return match.group(1)
    if _re.fullmatch(r'[a-zA-Z0-9_-]{10,}', raw):
        return raw
    return raw  # let the API call fail with a meaningful error


def _sse_stream(job_id: str):
    """
    Generator that yields SSE events for a clone job.
    - Replays the full buffered log first (supports reconnect).
    - Then streams live events from the queue.
    - Sends a keepalive ping every SSE_PING_INTERVAL seconds.
    """
    with _clone_jobs_lock:
        job = _clone_jobs.get(job_id)
    if not job:
        yield 'data: {"type":"error","msg":"Job not found"}\n\n'
        return

    # Replay history so a reconnecting client catches up
    with _clone_jobs_lock:
        history = list(job['log'])
    for evt in history:
        yield 'data: ' + json.dumps(evt, ensure_ascii=False) + '\n\n'

    # If job is already finished, stop here
    with _clone_jobs_lock:
        done = job['status'] in ('done', 'error')
    if done:
        return

    # Stream live events
    log_q: q_module.Queue = job['queue']
    while True:
        try:
            item = log_q.get(timeout=SSE_PING_INTERVAL)
            yield 'data: ' + json.dumps(item, ensure_ascii=False) + '\n\n'
            if item.get('type') in ('done', 'error'):
                break
        except q_module.Empty:
            yield 'data: {"type":"ping"}\n\n'


@app.route('/api/clone', methods=['POST'])
def api_clone():
    ds = _get_ds()
    if not ds:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.get_json() or {}
    raw_source = (data.get('source_id') or '').strip()
    dest_id    = (data.get('dest_folder_id') or 'root').strip()

    if not raw_source:
        return jsonify({'error': 'source_id is required'}), 400

    source_id = _parse_drive_folder_id(raw_source)
    job_id    = _uuid.uuid4().hex
    log_q: q_module.Queue = q_module.Queue()

    job = {'queue': log_q, 'status': 'running', 'log': []}
    with _clone_jobs_lock:
        _clone_jobs[job_id] = job

    def _record(evt: dict):
        """Persist event to history buffer and push to live queue."""
        with _clone_jobs_lock:
            job['log'].append(evt)
        log_q.put(evt)

    def run():
        def on_log(msg):
            if isinstance(msg, str):
                _record({'type': 'log', 'msg': msg})
            elif isinstance(msg, dict):
                # Structured events: quota_wait, quota_tick
                _record(msg)

        try:
            _record({'type': 'log', 'msg': f'🔍 Source ID: {source_id}'})
            _record({'type': 'log', 'msg': '🚀 Bắt đầu quét & clone...'})
            stats = ds.clone_folder_recursive(source_id, dest_id, on_log)
            with _clone_jobs_lock:
                job['status'] = 'done'
            _record({'type': 'done', 'stats': stats})
        except Exception as exc:
            with _clone_jobs_lock:
                job['status'] = 'error'
            _record({'type': 'error', 'msg': str(exc)})

    threading.Thread(target=run, daemon=True).start()

    def generate():
        # Send job_id first so frontend can store it for reconnect
        yield 'data: ' + json.dumps({'type': 'job_id', 'job_id': job_id}) + '\n\n'
        yield from _sse_stream(job_id)

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        },
    )


@app.route('/api/clone/<job_id>/stream')
def api_clone_stream(job_id: str):
    """Reconnect endpoint — replays buffered log then streams live events."""
    ds = _get_ds()
    if not ds:
        return jsonify({'error': 'Not authenticated'}), 401
    return Response(
        _sse_stream(job_id),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        },
    )


@app.route('/api/clone/<job_id>/status')
def api_clone_status(job_id: str):
    """Lightweight poll endpoint — returns job status + stats if done."""
    with _clone_jobs_lock:
        job = _clone_jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    resp: dict = {'status': job['status']}
    if job['status'] == 'done':
        with _clone_jobs_lock:
            for evt in reversed(job['log']):
                if evt.get('type') == 'done':
                    resp['stats'] = evt.get('stats')
                    break
    return jsonify(resp)
