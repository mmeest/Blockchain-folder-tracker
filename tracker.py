import hashlib
import json
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

BLOCKCHAIN_FILE = 'blockchain.json'
THROTTLE_SECONDS = 5  # min aeg kahe sama faili sündmuse vahel
ALLOWED_EXTENSIONS = {'.txt', '.py', '.md'}  # jälgitavad failitüübid

last_handled = {}

def calculate_hash(index, timestamp, data, previous_hash):
    value = f"{index}{timestamp}{data}{previous_hash}".encode()
    return hashlib.sha256(value).hexdigest()

def load_blockchain():
    if not os.path.exists(BLOCKCHAIN_FILE):
        return []
    with open(BLOCKCHAIN_FILE, 'r') as f:
        return json.load(f)
    
def save_blockchain(blockchain):
    with open(BLOCKCHAIN_FILE, 'w') as f:
        json.dump(blockchain, f, indent=2)

def create_block(data, blockchain): 
    index = len(blockchain) 
    timestamp = time.time()
    previous_hash = blockchain[-1]['hash'] if blockchain else '0'
    hash_val = calculate_hash(index, timestamp, data, previous_hash)
    block = {
        'index': index,
        'timestamp': timestamp,
        'data': data,
        'previous_hash': previous_hash,
        'hash': hash_val
    }   
    blockchain.append(block)
    save_blockchain(blockchain)

def should_handle_event(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False
    now = time.time()
    last_time = last_handled.get(file_path, 0)
    if now - last_time < THROTTLE_SECONDS:
        return False
    last_handled[file_path] = now
    return True

class WatcherHandler(FileSystemEventHandler):
    def handle_event(self, event_type, file_path, extra=None):
        if should_handle_event(file_path):
            data = {"event": event_type, "file": file_path}
            if extra:
                data.update(extra)
            create_block(data, blockchain)
            print(f"{event_type}: {file_path}")

    def on_created(self, event):
        if not event.is_directory:
            self.handle_event("created", event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            self.handle_event("deleted", event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.handle_event("modified", event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self.handle_event("moved", event.dest_path, {"src": event.src_path})

if __name__ == "__main__":
    path = os.getcwd()
    print(f"Jälgitakse kataloogi: {path}")
    blockchain = load_blockchain()
    event_handler = WatcherHandler()
    observer = Observer()
    observer.schedule(event_handler, path=path, recursive=False)  # ainult 1 kataloog
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
