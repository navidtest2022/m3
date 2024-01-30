import requests

def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json')
        ip_data = response.json()
        return ip_data['ip']
    except requests.RequestException as e:
        print(f"Error: {e}")
        return None

public_ip = get_public_ip()
if public_ip:
    print(f"My Public IP Address is: {public_ip}")
else:
    print("Could not retrieve the public IP address.")
