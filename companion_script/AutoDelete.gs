/**
 * AutoDelete.gs — Companion Apps Script for Drive Share Manager
 *
 * HOW TO SET UP (one-time only):
 * 1. Go to script.google.com → New Project
 * 2. Paste this entire file into the editor
 * 3. Click Run once to grant permissions
 * 4. Go to Triggers (clock icon) → Add Trigger:
 *    - Function: autoDeleteExpiredFolders
 *    - Event source: Time-driven
 *    - Type: Hour timer
 *    - Every: 1 hour
 * 5. Done! Folders will auto-delete even when the desktop app is closed.
 *
 * The desktop app writes a queue file "_share_manager_queue.json" to
 * the root of your Google Drive. This script reads it every hour and
 * deletes any folders whose expiry time has passed.
 */

var QUEUE_FILENAME = "_share_manager_queue.json";

/**
 * Main function — called by the time-based trigger every hour.
 * Reads the deletion queue and removes expired folders.
 */
function autoDeleteExpiredFolders() {
  var queue = readQueue();
  if (!queue || queue.length === 0) {
    Logger.log("Queue is empty, nothing to do.");
    return;
  }

  var now = new Date();
  var remaining = [];
  var deleted = [];
  var errors = [];

  queue.forEach(function(entry) {
    var expiresAt = new Date(entry.expires_at);
    if (now >= expiresAt) {
      // Time to delete!
      try {
        var folder = DriveApp.getFolderById(entry.folder_id);
        folder.setTrashed(true);
        deleted.push(entry.folder_name);
        Logger.log("✅ Deleted: " + entry.folder_name + " (ID: " + entry.folder_id + ")");
      } catch (e) {
        // Folder may already be deleted — just remove from queue
        Logger.log("⚠️ Could not delete (may already be gone): " + entry.folder_name + " — " + e.message);
        errors.push(entry.folder_name + ": " + e.message);
      }
    } else {
      remaining.push(entry);
    }
  });

  writeQueue(remaining);

  Logger.log("=== AutoDelete Run at " + now.toISOString() + " ===");
  Logger.log("Deleted: " + deleted.length + " folders");
  Logger.log("Remaining in queue: " + remaining.length + " folders");
  if (errors.length > 0) {
    Logger.log("Errors: " + errors.join(", "));
  }
}

/**
 * Read the deletion queue JSON file from Drive root.
 * Returns an array of entries or [] if not found.
 */
function readQueue() {
  var files = DriveApp.getRootFolder().getFilesByName(QUEUE_FILENAME);
  if (!files.hasNext()) {
    return [];
  }
  var file = files.next();
  try {
    var content = file.getBlob().getDataAsString("UTF-8");
    return JSON.parse(content);
  } catch (e) {
    Logger.log("Error reading queue file: " + e.message);
    return [];
  }
}

/**
 * Write the updated queue back to Drive.
 */
function writeQueue(queue) {
  var content = JSON.stringify(queue, null, 2);
  var files = DriveApp.getRootFolder().getFilesByName(QUEUE_FILENAME);
  if (files.hasNext()) {
    var file = files.next();
    file.setContent(content);
  } else {
    // Create the file if it somehow doesn't exist
    DriveApp.getRootFolder().createFile(QUEUE_FILENAME, content, "application/json");
  }
}

/**
 * Utility: Manually run this to see what's currently in the queue.
 * Useful for debugging.
 */
function showQueue() {
  var queue = readQueue();
  Logger.log("Current queue (" + queue.length + " entries):");
  queue.forEach(function(entry) {
    var expiresAt = new Date(entry.expires_at);
    var now = new Date();
    var remaining = Math.round((expiresAt - now) / 1000 / 60);
    Logger.log(
      "  📁 " + entry.folder_name +
      " | Hết hạn sau: " + remaining + " phút" +
      " | ID: " + entry.folder_id
    );
  });
}
