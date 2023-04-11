import os
import shutil
import sys
import time
import argparse
import hashlib

# CMD ARGS
parser = argparse.ArgumentParser(description='Sync two folders')
parser.add_argument('source', type=str, help='Source directory path')
parser.add_argument('replica', type=str, help='Replica directory path')
parser.add_argument('interval', type=int, help='Sync interval in seconds')
parser.add_argument('log', type=str, help='Log file path')
args = parser.parse_args()

sync_count = 0


# LOGGING
def logging(msg):
    with open(args.log, 'a') as log_file:
        log_file.write(f'{msg}\n')
    print(msg)


# MAIN SYNC
def sync():
    global sync_count
    files_dirs_added = 0
    files_dirs_changed = 0
    files_dirs_removed = 0
    sync_count = sync_count + 1
    logging(f'*** Starting sync run {sync_count} ***')
    # Walk through source directory and copy all to replica directory
    for root, dirs, files in os.walk(args.source):
        replica_root = root.replace(args.source, args.replica)
        # Match directory structure
        for dir_name in dirs:
            replica_dir = os.path.join(replica_root, dir_name)
            if not os.path.exists(replica_dir):
                os.makedirs(replica_dir)
                files_dirs_added = files_dirs_added + 1
                logging(f'Created directory: {replica_dir}')
        for file_name in files:
            source_file = os.path.join(root, file_name)
            replica_file = os.path.join(replica_root, file_name)
            if os.path.exists(replica_file):
                # Check MD5 hash
                source_hash = hashlib.md5(open(source_file, 'rb').read()).hexdigest()
                replica_hash = hashlib.md5(open(replica_file, 'rb').read()).hexdigest()
                # Compare source and replica file hashes
                if source_hash != replica_hash:
                    shutil.copy2(source_file, replica_file)
                    files_dirs_changed = files_dirs_changed + 1
                    logging(f'Updated file: {replica_file}')
            else:
                shutil.copy2(source_file, replica_file)
                files_dirs_added = files_dirs_added + 1
                logging(f'Created file: {replica_file}')
    # Remove files & folders from replica that are not in source directory (sync match)
    for root, dirs, files in os.walk(args.replica):
        source_root = root.replace(args.replica, args.source)
        for dir_name in dirs:
            source_dir = os.path.join(source_root, dir_name)
            if not os.path.exists(source_dir):
                shutil.rmtree(os.path.join(root, dir_name))
                logging(f'Removed directory: {os.path.join(root, dir_name)}, not present in source directory')
                files_dirs_removed = files_dirs_removed + 1
        for file_name in files:
            source_file = os.path.join(source_root, file_name)
            replica_file = os.path.join(root, file_name)
            if not os.path.exists(source_file):
                os.remove(replica_file)
                logging(f'Removed file: {replica_file}, not present in source directory')
                files_dirs_removed = files_dirs_removed + 1
    logging(f'*** Finished sync run {sync_count} *** \n'
            '*** Post Sync Report *** \n'
            f'Files & Folders added: {files_dirs_added} \n'
            f'Files & Folders changed: {files_dirs_changed} \n'
            f'Files & Folders removed: {files_dirs_removed} \n')


while True:
    try:
        sync()
        time.sleep(args.interval)
    except KeyboardInterrupt:
        print(f'*** Interrupted by user on sync run {sync_count} ***')
        print(f'Full log can be found at: {args.log}')
        sys.exit(130)
