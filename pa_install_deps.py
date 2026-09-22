import requests
import time

USERNAME = "MediNEXA"
API_TOKEN = "f33e313510a63b3c26e78db93e71b053ce9ac8fa"
DOMAIN = "MediNEXA.pythonanywhere.com"

headers = {"Authorization": f"Token {API_TOKEN}"}

# Create a bash console to run pip install resend
console_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/"
res = requests.post(console_url, headers=headers, json={"executable": "bash"})
if res.status_code == 201:
    console_id = res.json().get("id")
    print(f"Bash console created: ID {console_id}")
    time.sleep(2)
    
    # Send pip install command and deploy script
    input_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{console_id}/send_input/"
    requests.post(input_url, headers=headers, json={"input": "pip3 install --user resend\n"})
    time.sleep(5)
    
    # Reload webapp
    requests.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/", headers=headers)
    print(" Resend package setup & Webapp Reloaded successfully!")
else:
    print(f"Console info: {res.status_code} - {res.text}")
