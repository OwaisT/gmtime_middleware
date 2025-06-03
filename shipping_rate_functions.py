import os
import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

consumer_key = os.environ.get("CONSUMER_KEY")
consumer_secret = os.environ.get("CONSUMER_SECRET")
base_url = os.environ.get("BASE_URL")

auth = HTTPBasicAuth(consumer_key, consumer_secret)

def get_shipping_rate():
    url = f"{base_url}products/772"
    response = requests.get(url, auth=auth)
    if response.status_code == 200:
        raw_rate = response.json()
        return raw_rate["price"]
    else:
        return None