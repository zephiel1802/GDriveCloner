"""
Google Drive Service — wraps all Drive API calls.
"""
import datetime
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

    def _find_queue_file(self) -> str | None:
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
