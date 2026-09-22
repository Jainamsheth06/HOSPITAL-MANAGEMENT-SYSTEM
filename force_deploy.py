import requests, time

USERNAME = 'MediNEXA'
API_TOKEN = 'f33e313510a63b3c26e78db93e71b053ce9ac8fa'
headers = {'Authorization': f'Token {API_TOKEN}'}

# 1. Delete all existing consoles to prevent 'blocked console' issues
consoles_url = f'https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/'
res = requests.get(consoles_url, headers=headers)
if res.status_code == 200:
    for c in res.json():
        print(f"Deleting console {c['id']}")
        requests.delete(f"{consoles_url}{c['id']}/", headers=headers)

# 2. Create a fresh console
print('Creating new console...')
create_res = requests.post(consoles_url, headers=headers, json={'executable': 'bash'})
console_id = create_res.json()['id']
print(f'Created console {console_id}')

# 3. Send the unzip command
cmd = (
    "cd /home/MediNEXA && "
    "rm -rf hms_app owner_app hos_project cloudflare_worker && "
    "unzip -o final_update.zip && "
    "echo '=== UNZIP COMPLETE ===' \n"
)
send_url = f'https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{console_id}/send_input/'
requests.post(send_url, headers=headers, json={'input': cmd})

print('Waiting for unzip...')
for _ in range(15):
    time.sleep(2)
    out = requests.get(f'https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{console_id}/get_latest_output/', headers=headers).json().get('output', '')
    if '=== UNZIP COMPLETE ===' in out:
        print('Unzip successful!')
        break
else:
    print('Unzip might not have finished.')

# 4. Reload webapp
print('Reloading webapp...')
DOMAIN = 'MediNEXA.pythonanywhere.com'
reload_url = f'https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/'
requests.post(reload_url, headers=headers)
print('Done!')
