"""
Google Drive Service — wraps all Drive API calls.
"""
import datetime
from typing import Optional
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


class DriveService:
    def __init__(self, creds: Credentials):
        self.service = build("drive", "v3", credentials=creds)

    # ──────────────────────────────────────────────
    # Folder browsing
    # ──────────────────────────────────────────────

    def list_folders(self, parent_id: str = "root") -> list[dict]:
        """
        List direct subfolder children of a given folder.
        Returns list of {id, name}.
        """
        query = (
            f"'{parent_id}' in parents "
            "and mimeType = 'application/vnd.google-apps.folder' "
            "and trashed = false"
        )
        results = []
        page_token = None
        while True:
            resp = self.service.files().list(
                q=query,
                spaces="drive",
                fields="nextPageToken, files(id, name)",
                orderBy="name",
                pageToken=page_token,
            ).execute()
            results.extend(resp.get("files", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
        return results

    def list_files_in_folder(self, folder_id: str) -> list[dict]:
        """List all non-folder files in a folder."""
        query = (
            f"'{folder_id}' in parents "
            "and mimeType != 'application/vnd.google-apps.folder' "
            "and trashed = false"
        )
        results = []
        page_token = None
        while True:
            resp = self.service.files().list(
                q=query,
                spaces="drive",
                fields="nextPageToken, files(id, name, mimeType, size)",
                orderBy="name",
                pageToken=page_token,
            ).execute()
            results.extend(resp.get("files", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
        return results

    def get_folder_name(self, folder_id: str) -> str:
        """Get the name of a folder by ID."""
        if folder_id == "root":
            return "My Drive"
        try:
            f = self.service.files().get(
                fileId=folder_id, fields="name"
            ).execute()
            return f.get("name", folder_id)
        except Exception:
            return folder_id

    # ──────────────────────────────────────────────
    # Temp folder creation & sharing
    # ──────────────────────────────────────────────

    def create_folder(self, name: str, parent_id: str = "root") -> dict:
        """Create a new folder and return its metadata {id, name, webViewLink}."""
        metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        }
        folder = self.service.files().create(
            body=metadata,
            fields="id, name, webViewLink",
        ).execute()
        return folder

    def copy_files_from_folder(
        self, source_folder_id: str, dest_folder_id: str,
        progress_callback=None
    ) -> list[dict]:
        """
        Copy all files from source_folder_id into dest_folder_id.
        Calls progress_callback(copied, total) after each copy.
        Returns list of copied file metadata.
        """
        files = self.list_files_in_folder(source_folder_id)
        copied = []
        for i, file in enumerate(files):
            body = {
                "name": file["name"],
                "parents": [dest_folder_id],
            }
            result = self.service.files().copy(
                fileId=file["id"], body=body, fields="id, name"
            ).execute()
            copied.append(result)
            if progress_callback:
                progress_callback(i + 1, len(files))
        return copied

    def set_folder_public_share(self, folder_id: str):
        """Make a folder viewable by anyone with the link."""
        permission = {
            "type": "anyone",
            "role": "reader",
        }
        self.service.permissions().create(
            fileId=folder_id,
            body=permission,
        ).execute()

    def get_folder_link(self, folder_id: str) -> str:
        """Return the shareable web view link of a folder."""
        f = self.service.files().get(
            fileId=folder_id, fields="webViewLink"
        ).execute()
        return f.get("webViewLink", "")

    # ──────────────────────────────────────────────
    # Deletion
    # ──────────────────────────────────────────────

    def delete_folder(self, folder_id: str):
        """Permanently delete a folder."""
        self.service.files().delete(fileId=folder_id).execute()

    def folder_exists(self, folder_id: str) -> bool:
        """Check whether a folder still exists (not trashed, not deleted)."""
        try:
            f = self.service.files().get(
                fileId=folder_id, fields="id, trashed"
            ).execute()
            return not f.get("trashed", False)
        except Exception:
            return False

    # ──────────────────────────────────────────────
    # Queue file management
    # ──────────────────────────────────────────────

    QUEUE_FILENAME = "_share_manager_queue.json"

    def _find_queue_file(self) -> Optional[str]:
        """Find the queue JSON file in root, return its ID or None."""
        query = (
            f"name = '{self.QUEUE_FILENAME}' "
            "and 'root' in parents "
            "and trashed = false"
        )
        resp = self.service.files().list(
            q=query, fields="files(id)"
        ).execute()
        files = resp.get("files", [])
        return files[0]["id"] if files else None

    def read_queue(self) -> list[dict]:
        """Read the deletion queue from Drive. Returns [] if not found."""
        import io, json
        file_id = self._find_queue_file()
        if not file_id:
            return []
        content = self.service.files().get_media(fileId=file_id).execute()
        return json.loads(content.decode("utf-8"))

    def write_queue(self, queue: list[dict]):
        """Write/update the deletion queue JSON file on Drive."""
        import io, json
        from googleapiclient.http import MediaIoBaseUpload

        content = json.dumps(queue, ensure_ascii=False, indent=2).encode("utf-8")
        media = MediaIoBaseUpload(
            io.BytesIO(content), mimetype="application/json", resumable=False
        )
        file_id = self._find_queue_file()
        if file_id:
            self.service.files().update(
                fileId=file_id, media_body=media
            ).execute()
        else:
            metadata = {
                "name": self.QUEUE_FILENAME,
                "parents": ["root"],
                "mimeType": "application/json",
            }
            self.service.files().create(
                body=metadata, media_body=media, fields="id"
            ).execute()

    def add_to_queue(self, folder_id: str, folder_name: str, expires_at: datetime.datetime):
        """Add a folder to the deletion queue."""
        queue = self.read_queue()
        # Remove any existing entry with same folder_id
        queue = [e for e in queue if e.get("folder_id") != folder_id]
        queue.append({
            "folder_id": folder_id,
            "folder_name": folder_name,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        })
        self.write_queue(queue)

    def remove_from_queue(self, folder_id: str):
        """Remove a folder entry from the deletion queue."""
        queue = self.read_queue()
        queue = [e for e in queue if e.get("folder_id") != folder_id]
        self.write_queue(queue)

    # ──────────────────────────────────────────────
    # Clone (copy shared → own Drive) with resume
    # ──────────────────────────────────────────────

    # Quota-error status codes from the Drive API
    _QUOTA_STATUS_CODES = {429, 403}
    # Max seconds to wait during exponential backoff
    _MAX_BACKOFF = 300

    def get_existing_items(self, folder_id: str) -> dict:
        """
        Return a dict keyed by (name, is_folder) → file_id for all
        non-trashed children of folder_id.  Used for resume/skip logic.
        """
        items: dict = {}
        page_token = None
        while True:
            query = f"'{folder_id}' in parents and trashed=false"
            resp = self.service.files().list(
                q=query,
                fields="nextPageToken, files(id, name, mimeType)",
                pageSize=1000,
                pageToken=page_token,
            ).execute()
            for f in resp.get("files", []):
                is_folder = (f["mimeType"] == "application/vnd.google-apps.folder")
                items[(f["name"], is_folder)] = f["id"]
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
        return items

    def _copy_with_backoff(
        self,
        file_id: str,
        body: dict,
        log_callback=None,
        max_retries: int = 6,
    ) -> dict:
        """
        Copy a file with exponential backoff on quota / rate-limit errors.
        Sends { type: 'quota_wait', seconds: N } events via log_callback
        so the frontend can show a live countdown.
        Raises the last exception if all retries are exhausted.
        """
        import time as _time

        try:
            from googleapiclient.errors import HttpError
        except ImportError:
            HttpError = Exception  # fallback

        delay = 5  # initial wait in seconds
        for attempt in range(max_retries + 1):
            try:
                return self.service.files().copy(
                    fileId=file_id, body=body
                ).execute()
            except HttpError as exc:
                status = getattr(exc, 'resp', None)
                status_code = int(status.status) if status else 0
                is_quota = status_code in self._QUOTA_STATUS_CODES

                if not is_quota or attempt == max_retries:
                    raise

                wait = min(delay * (2 ** attempt), self._MAX_BACKOFF)
                if log_callback:
                    log_callback({
                        'type': 'quota_wait',
                        'seconds': wait,
                        'attempt': attempt + 1,
                        'msg': f'  ⏳ Quota exceeded — chờ {wait}s rồi retry (lần {attempt + 1}/{max_retries})...',
                    })
                # tick down every second so frontend can animate countdown
                for remaining in range(wait, 0, -1):
                    _time.sleep(1)
                    if log_callback:
                        log_callback({'type': 'quota_tick', 'remaining': remaining - 1})
            except Exception:
                raise

        raise RuntimeError('Unreachable')

    def clone_folder_recursive(
        self,
        source_folder_id: str,
        dest_parent_id: str,
        log_callback=None,
        _stats: "dict | None" = None,
    ) -> dict:
        """
        Recursively clone source_folder_id into dest_parent_id.
        Skips files / folders that already exist (resume-safe).
        Uses exponential backoff on quota errors.

        log_callback receives either a plain str or a dict:
          str  → log line
          dict → structured event (quota_wait, quota_tick)
        Returns stats dict { copied, skipped, folders_created, errors }.
        """
        import time as _time

        if _stats is None:
            _stats = {"copied": 0, "skipped": 0, "folders_created": 0, "errors": 0}

        def _log(msg):
            if log_callback:
                log_callback(msg)

        # --- snapshot of what already exists at destination ---
        existing = self.get_existing_items(dest_parent_id)

        page_token = None
        while True:
            query = f"'{source_folder_id}' in parents and trashed=false"
            resp = self.service.files().list(
                q=query,
                fields="nextPageToken, files(id, name, mimeType)",
                pageSize=1000,
                pageToken=page_token,
            ).execute()

            for item in resp.get("files", []):
                is_folder = (item["mimeType"] == "application/vnd.google-apps.folder")
                key = (item["name"], is_folder)

                if is_folder:
                    if key in existing:
                        dest_folder_id = existing[key]
                        _log(f"📁 Thư mục đã có: {item['name']} → Đang quét bên trong...")
                    else:
                        meta = {
                            "name": item["name"],
                            "mimeType": "application/vnd.google-apps.folder",
                            "parents": [dest_parent_id],
                        }
                        new_folder = self.service.files().create(
                            body=meta, fields="id"
                        ).execute()
                        dest_folder_id = new_folder["id"]
                        _stats["folders_created"] += 1
                        _log(f"📁 Đã TẠO MỚI thư mục: {item['name']}")

                    # recurse
                    self.clone_folder_recursive(
                        item["id"], dest_folder_id, log_callback, _stats
                    )

                else:
                    if key in existing:
                        _stats["skipped"] += 1
                        _log(f"  ⏩ Đã tồn tại, BỎ QUA: {item['name']}")
                    else:
                        file_meta = {
                            "name": item["name"],
                            "parents": [dest_parent_id],
                        }
                        try:
                            self._copy_with_backoff(
                                item["id"], file_meta, log_callback
                            )
                            _stats["copied"] += 1
                            _log(f"  📄 Đã COPY MỚI: {item['name']}")
                        except Exception as exc:
                            _stats["errors"] += 1
                            _log(f"  ❌ Lỗi khi copy {item['name']}: {exc}")
                        _time.sleep(0.1)   # light throttle between copies

            page_token = resp.get("nextPageToken")
            if not page_token:
                break

        return _stats
