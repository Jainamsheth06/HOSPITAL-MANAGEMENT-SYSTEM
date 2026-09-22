import os
import zipfile

# Files and directories to package into final_update.zip
base_dir = os.path.dirname(os.path.abspath(__file__))
zip_filename = os.path.join(base_dir, 'final_update.zip')

include_dirs = ['hms_app', 'owner_app', 'hos_project', 'static']
include_files = ['.env', 'requirements.txt', 'manage.py', 'deploy.sh']

print(f"Creating {zip_filename}...")
with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
    # Add root files
    for fname in include_files:
        fpath = os.path.join(base_dir, fname)
        if os.path.exists(fpath):
            zipf.write(fpath, fname)
            print(f"Added file: {fname}")

    # Add directories
    for dname in include_dirs:
        dpath = os.path.join(base_dir, dname)
        if os.path.exists(dpath):
            for root, dirs, files in os.walk(dpath):
                # skip __pycache__
                if '__pycache__' in root:
                    continue
                for file in files:
                    if file.endswith('.pyc'):
                        continue
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, base_dir)
                    zipf.write(full_path, rel_path)
                    print(f"Added: {rel_path}")

print(" final_update.zip created successfully!")
