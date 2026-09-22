import os
import requests
import zipfile

USERNAME = "MediNEXA"
API_TOKEN = "f33e313510a63b3c26e78db93e71b053ce9ac8fa"
DOMAIN = "MediNEXA.pythonanywhere.com"

headers = {
    "Authorization": f"Token {API_TOKEN}"
}

base_dir = os.path.dirname(os.path.abspath(__file__))

def upload_file_to_pa(local_path, remote_path):
    url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{remote_path}"
    with open(local_path, "rb") as f:
        response = requests.post(url, headers=headers, files={"content": f})
    if response.status_code in (200, 201):
        print(f" Uploaded: {remote_path}")
        return True
    else:
        print(f" Failed upload {remote_path}: {response.status_code} - {response.text}")
        return False

# 1. Upload final_update.zip
zip_path = os.path.join(base_dir, "final_update.zip")
if os.path.exists(zip_path):
    print("Uploading final_update.zip...")
    upload_file_to_pa(zip_path, f"/home/{USERNAME}/final_update.zip")

# 2. Upload individual key modified files directly to ensure instant sync
files_to_sync = [
    (".env", f"/home/{USERNAME}/.env"),
    ("requirements.txt", f"/home/{USERNAME}/requirements.txt"),
    ("hos_project/settings.py", f"/home/{USERNAME}/hos_project/settings.py"),
    ("hms_app/notifications.py", f"/home/{USERNAME}/hms_app/notifications.py"),
]

for local_rel, remote_p in files_to_sync:
    local_abs = os.path.join(base_dir, local_rel.replace("/", os.sep))
    if os.path.exists(local_abs):
        upload_file_to_pa(local_abs, remote_p)

# 3. Reload Web App
print(f"Reloading webapp {DOMAIN}...")
reload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/"
reload_res = requests.post(reload_url, headers=headers)
if reload_res.status_code in (200, 201):
    print(" Webapp successfully reloaded and LIVE on PythonAnywhere!")
else:
    print(f" Reload status: {reload_res.status_code} - {reload_res.text}")
