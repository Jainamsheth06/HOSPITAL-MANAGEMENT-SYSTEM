import os
import requests
import time

USERNAME = "MediNEXA"
API_TOKEN = "f33e313510a63b3c26e78db93e71b053ce9ac8fa"

headers = {"Authorization": f"Token {API_TOKEN}"}
base_dir = os.path.dirname(os.path.abspath(__file__))

# 1. Upload test_pa_live_email.py
url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/home/{USERNAME}/test_pa_live_email.py"
with open(os.path.join(base_dir, "test_pa_live_email.py"), "rb") as f:
    requests.post(url, headers=headers, files={"content": f})

# 2. Get active console
consoles_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/"
res = requests.get(consoles_url, headers=headers)
consoles = res.json()
if consoles:
    console_id = consoles[0]["id"]
    # Send python test_pa_live_email.py command
    send_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{console_id}/send_input/"
    requests.post(send_url, headers=headers, json={"input": "cd /home/MediNEXA && python test_pa_live_email.py\n"})
    time.sleep(6)
    
    # Read output
    output_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{console_id}/get_latest_output/"
    out_res = requests.get(output_url, headers=headers)
    print("Console output:\n", out_res.json().get("output", ""))
