import requests
from dotenv import load_dotenv
import os
load_dotenv(override=True)

url="http://127.0.0.1:5000/v1/"
header = {
    "Authorization":f"Bearer {os.environ.get('API_KEY')}",
    "Content-Type":"application/json"
}
parameters= {
    "id":6
}
response = requests.get(url=url+"history_images",headers=header)
print(response.status_code)
print(response.text)
print(response.json())