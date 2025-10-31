import mimetypes
import sys 
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from image_search import ImageSearcher
import os
import time
from win11toast import toast
class ImageFileHandler(FileSystemEventHandler):
    def __init__(self, searcher_instance):
        self.imagesearcher = searcher_instance
        print("ImageFileHandler initialized. Ready to watch...")

    def on_created(self, event):
        if event.is_directory:
            return
        
        mimetype, _ = mimetypes.guess_type(event.src_path)
        
        if mimetype and mimetype.startswith("image/"):
            toast("Image Searcher" , f"Processing new image {os.path.normpath(event.src_path)} " , duration = "short")
            time.sleep(1)
            self.imagesearcher.process_dir(os.path.normpath(event.src_path) , via_background=True)
            toast("Image Searcher" , f"New image added: {os.path.normpath(event.src_path)} " , duration = "short")

if __name__ == "__main__":
    
    print("Starting Watcher Service...")
    
    master_searcher = ImageSearcher()
    
    event_handler = ImageFileHandler(master_searcher)
    
    observer = Observer()
    
    directories_to_watch = master_searcher.linked_directories

    if not directories_to_watch:
        print("No directories are linked. Watcher will not start.")
        print(f"Run 'python manage_links.py' to add directories.")
        sys.exit()

    print("---")
    for path in directories_to_watch:
        if os.path.exists(path):
            observer.schedule(event_handler, path, recursive=True)
            print(f"🚀 Observer scheduled for: {path}")
        else:
            print(f"Warning: Linked path not found. Skipping: {path}")
    print("---")
        
    observer.start()
    print("\nObserver started. Waiting for new images...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping watcher...")
        observer.stop()
    
    observer.join()
    print("Watcher stopped.")