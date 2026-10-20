"""
File Watcher Service Module

This module provides utilities for monitoring and representing the file system structure
in the EnCompliance application. It includes logic for generating file trees and (optionally)
watching directories for changes.

Key functionalities:
- File tree generation for directories
- File and directory metadata extraction
- Error handling for file system access
- (Optional) Watchdog-based directory monitoring
- File tree caching for performance

Dependencies:
- pathlib: For file system path operations
- datetime: For timestamp handling
- json: For file tree serialization
- (Optional) watchdog: For real-time file system monitoring
"""

import os
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Note: watchdog is an external dependency, ensure it's in requirements.txt
# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler

# --- File Tree Generation Logic ---

def get_file_tree(start_path: str) -> Dict[str, Any]:
    """Generates a nested dictionary representing the file structure.
    
    Args:
        start_path: The root directory path to scan.

    Returns:
        A dictionary representing the file tree including name, type, 
        size (for files), and last modified timestamp.
    """
    start_path_obj = Path(start_path)
    if not start_path_obj.is_dir():
        raise ValueError(f"Path is not a valid directory: {start_path}")

    def _build_tree(current_path: Path) -> Dict[str, Any]:
        try:
            stat_info = current_path.stat()
            is_dir = current_path.is_dir()
            tree = {
                "name": current_path.name,
                "type": "directory" if is_dir else "file",
                "last_modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "path": str(current_path) # Include the full path for clarity
            }
            if is_dir:
                tree["children"] = [
                    _build_tree(child) 
                    for child in sorted(current_path.iterdir()) 
                    # Add filtering if needed (e.g., exclude .git, __pycache__, node_modules)
                    if child.name not in [".git", "__pycache__", "node_modules", ".DS_Store"]
                ]
            else:
                tree["size"] = stat_info.st_size
            return tree
        except OSError as e:
            # Handle permission errors or other OS issues gracefully
            return {
                "name": current_path.name,
                "type": "error",
                "error": str(e),
                 "path": str(current_path)
            }

    return _build_tree(start_path_obj)

# --- Watchdog Implementation (Optional - Can be run as a separate process) ---
# If you want continuous monitoring, you would uncomment and adapt this section.
# It would likely run as a background task or separate microservice.

# class FileTreeCacheHandler(FileSystemEventHandler):
#     def __init__(self, cache_file='file_tree_cache.json', monitored_paths=None):
#         self.cache_file = cache_file
#         self.monitored_paths = monitored_paths or ['./encompliance-backend', './encompliance-frontend', './storage']
#         self.update_cache()

#     def on_any_event(self, event):
#         # Basic trigger: update cache on any filesystem event in monitored paths
#         # More sophisticated logic could filter events or debounce updates
#         print(f"Detected change: {event.event_type} at {event.src_path}. Updating cache...")
#         self.update_cache()

#     def update_cache(self):
#         full_tree = {}
#         for path in self.monitored_paths:
#             try:
#                 # Use a key for each monitored root path
#                 root_name = Path(path).name or 'root' # Handle case where path is '.'
#                 full_tree[root_name] = get_file_tree(path)
#             except ValueError as e:
#                 print(f"Error scanning path {path}: {e}")
#                 full_tree[root_name] = {"error": str(e)}
        
#         try:
#             with open(self.cache_file, 'w') as f:
#                 json.dump(full_tree, f, indent=2)
#             print(f"File tree cache updated: {self.cache_file}")
#         except IOError as e:
#             print(f"Error writing cache file: {e}")

# def start_file_watcher(paths_to_watch, cache_file):
#     event_handler = FileTreeCacheHandler(cache_file=cache_file, monitored_paths=paths_to_watch)
#     observer = Observer()
#     for path in paths_to_watch:
#         observer.schedule(event_handler, path, recursive=True)
#         print(f"Watching directory: {path}")
    
#     observer.start()
#     print("File watcher started.")
#     try:
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         observer.stop()
#         print("File watcher stopped.")
#     observer.join()

# Example Usage (if running watcher directly):
# if __name__ == "__main__":
#     project_root = Path(__file__).resolve().parents[2] # Assumes this file is in app/services/
#     paths = [
#         str(project_root / 'encompliance-backend'), 
#         str(project_root / 'encompliance-frontend'), 
#         str(project_root / 'storage')
#     ]
#     cache = project_root / 'file_tree_cache.json'
#     start_file_watcher(paths, str(cache)) 