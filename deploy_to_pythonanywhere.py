import os
import time
import requests
import zipfile

USERNAME = "MediNEXA"
API_TOKEN = "f33e313510a63b3c26e78db93e71b053ce9ac8fa"
DOMAIN = "MediNEXA.pythonanywhere.com"

headers = {"Authorization": f"Token {API_TOKEN}"}
base_dir = os.path.dirname(os.path.abspath(__file__))

print(" Starting deployment to PythonAnywhere...")

# 1. Package final_update.zip
zip_filename = os.path.join(base_dir, 'final_update.zip')
include_dirs = ['hms_app', 'owner_app', 'hos_project', 'static']
include_files = ['.env', 'requirements.txt', 'manage.py', 'deploy.sh']

print(f" Packaging files into {zip_filename}...")
with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for fname in include_files:
        fpath = os.path.join(base_dir, fname)
        if os.path.exists(fpath):
            zipf.write(fpath, fname)
    for dname in include_dirs:
        dpath = os.path.join(base_dir, dname)
        if os.path.exists(dpath):
            for root, dirs, files in os.walk(dpath):
                if '__pycache__' in root:
                    continue
                for file in files:
                    if file.endswith('.pyc'):
                        continue
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, base_dir)
                    zipf.write(full_path, rel_path)

print(" Zip created.")

# 2. Upload final_update.zip to PythonAnywhere
print(" Uploading final_update.zip to PythonAnywhere...")
zip_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/home/{USERNAME}/final_update.zip"
with open(zip_filename, "rb") as f:
    upload_res = requests.post(zip_url, headers=headers, files={"content": f})

if upload_res.status_code in (200, 201):
    print(" final_update.zip uploaded successfully.")
else:
    print(f" Zip upload failed: {upload_res.status_code} - {upload_res.text}")

# 3. Direct upload key files to ensure immediate sync
direct_files = [
    (".env", f"/home/{USERNAME}/.env"),
    ("requirements.txt", f"/home/{USERNAME}/requirements.txt"),
    ("hos_project/settings.py", f"/home/{USERNAME}/hos_project/settings.py"),
    ("hos_project/urls.py", f"/home/{USERNAME}/hos_project/urls.py"),
    ("hos_project/wsgi.py", f"/home/{USERNAME}/hos_project/wsgi.py"),
]
for local_rel, remote_p in direct_files:
    local_abs = os.path.join(base_dir, local_rel.replace("/", os.sep))
    if os.path.exists(local_abs):
        url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{remote_p}"
        with open(local_abs, "rb") as f:
            requests.post(url, headers=headers, files={"content": f})
print(" Direct key files synced.")

# 4. Use Console to unzip, install requirements, migrate, and collectstatic
consoles_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/"
res = requests.get(consoles_url, headers=headers)
consoles = res.json() if res.status_code == 200 else []

console_id = None
if consoles:
    console_id = consoles[0]["id"]
    print(f" Using existing console ID: {console_id}")
else:
    print(" Creating new Bash console...")
    create_res = requests.post(consoles_url, headers=headers, json={"executable": "bash"})
    if create_res.status_code == 201:
        console_id = create_res.json()["id"]
        print(f" Created console ID: {console_id}")

if console_id:
    cmd = (
        "cd /home/MediNEXA && "
        "unzip -o final_update.zip && "
        "pip3 install --user -r requirements.txt && "
        "python manage.py migrate --noinput && "
        "python manage.py collectstatic --noinput && "
        "echo '=== DEPLOYMENT_COMPLETE ==='\n"
    )
    send_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{console_id}/send_input/"
    requests.post(send_url, headers=headers, json={"input": cmd})
    print(" Running deployment commands in console (unzip, migrations, collectstatic)...")
    
    # Wait for completion
    for _ in range(6):
        time.sleep(3)
        out_res = requests.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{console_id}/get_latest_output/", headers=headers)
        if out_res.status_code == 200:
            out_text = out_res.json().get("output", "")
            if "=== DEPLOYMENT_COMPLETE ===" in out_text:
                print(" Remote commands finished successfully.")
                break

# 5. Reload webapp
print(f" Reloading webapp {DOMAIN}...")
reload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/"
reload_res = requests.post(reload_url, headers=headers)

if reload_res.status_code in (200, 201):
    print(" Webapp successfully reloaded!")
else:
    print(f" Webapp reload response: {reload_res.status_code} - {reload_res.text}")

# 6. Verify live site
time.sleep(2)
try:
    check_res = requests.get(f"https://{DOMAIN}", timeout=10)
    print(f" Site HTTP Status: {check_res.status_code}")
    if check_res.status_code == 200:
        print(" https://medinexa.pythonanywhere.com is LIVE and healthy!")
    else:
        print(f" Unexpected status code: {check_res.status_code}")
except Exception as e:
    print(f" Check error: {e}")
