import requests
import time

USERNAME = "MediNEXA"
API_TOKEN = "f33e313510a63b3c26e78db93e71b053ce9ac8fa"
DOMAIN = "MediNEXA.pythonanywhere.com"

headers = {"Authorization": f"Token {API_TOKEN}"}

# List consoles
consoles_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/"
res = requests.get(consoles_url, headers=headers)
print("Consoles list status:", res.status_code)
consoles = res.json()
print("Found consoles:", len(consoles))

if consoles:
    target_console = consoles[0]
    console_id = target_console["id"]
    print(f"Using console ID: {console_id}")
    
    # Send unzip, pip install and deploy commands
    commands = (
        "cd /home/MediNEXA && "
        "unzip -o final_update.zip && "
        "pip3 install --user resend && "
        "python manage.py collectstatic --noinput && "
        "echo '=== ALL UPDATES APPLIED ==='\n"
    )
    send_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{console_id}/send_input/"
    input_res = requests.post(send_url, headers=headers, json={"input": commands})
    print("Command sent status:", input_res.status_code)
    
    time.sleep(6)
    
    # Reload webapp
    reload_res = requests.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/", headers=headers)
    print("Webapp reload status:", reload_res.status_code)
    if reload_res.status_code in (200, 201):
        print(" Live PythonAnywhere webapp successfully reloaded and 100% updated!")
else:
    print("No existing consoles found.")
