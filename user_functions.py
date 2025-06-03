import os
import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

JWT_authenticate_URL = os.environ.get("JWT_authenticate_URL")
JWT_validate_URL = os.environ.get("JWT_validate_URL")
JWT_register_URL = os.environ.get("JWT_register_URL")
jwt_auth_key = os.environ.get("JWT_auth_key")
JWT_reset_URL = os.environ.get("JWT_reset_URL")
consumer_key = os.environ.get("CONSUMER_KEY")
consumer_secret = os.environ.get("CONSUMER_SECRET")
base_url = os.environ.get("BASE_URL")

authorisation = HTTPBasicAuth(consumer_key, consumer_secret)

def authenticate_user(data):
    email = data["email"]
    password = data["password"]
    url = f"{JWT_authenticate_URL}email={email}&password={password}&AUTH_KEY={jwt_auth_key}"
    response = requests.post(url)
    res_json = response.json()
    if(res_json["success"] == True):
        print(res_json)
        return res_json["data"]["jwt"]
    else:
        print("Error retrieving JWT")
        print(res_json)
        return None

def get_user_id(JWT_Token):
    if len(JWT_Token) > 0:
        url = f"{JWT_validate_URL}{JWT_Token}&AUTH_KEY={jwt_auth_key}"
        response = requests.post(url)
        res_json = response.json()
        if(res_json["success"] == True):
            user_id = res_json["data"]["user"]["ID"]
            return user_id
        else:
            print("Error retrieving user ID")
            print(res_json)
            return None

def get_user(user_token):
    user_id = get_user_id(user_token)
    url = f"{base_url}customers/{user_id}"
    response = requests.get(url, auth=authorisation)
    if response.status_code == 200:
        fetched_user = response.json()
        return organize_user_to_send(fetched_user)
    else:
        return None
    
def organize_user_to_send(whole_user):
    user = {}
    user["billing"] = whole_user["billing"]
    user["email"] = whole_user["email"]
    user["first_name"] = whole_user["first_name"]
    user["id"] = whole_user["id"]
    user["last_name"] = whole_user["last_name"]
    user["shipping"] = whole_user["shipping"]
    return user

def create_user(user_data):
    first_name = user_data["first_name"]
    last_name = user_data["last_name"]
    email = user_data["email"]
    password = user_data["password"]
    phone = user_data["phone"]
    username = user_data["email"]
    url = f"{JWT_register_URL}email={email}&first_name={first_name}&last_name={last_name}&password={password}&phone={phone}&user_login={username}&AUTH_KEY={jwt_auth_key}"
    response = requests.post(url)
    res_json = response.json()
    if(res_json["success"] == True):
        user_token = authenticate_user(user_data)
        return user_token
    else:
        print("Error creating user")
        print(res_json)
        return None

def reset_password(data):
    email = data["email"]
    try:
        url = f"{JWT_reset_URL}email={email}&AUTH_KEY={jwt_auth_key}"
        response = requests.post(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        res_json = response.json()
    except requests.exceptions.RequestException as e:
        print(f"HTTP request failed: {e}")
        return "Wrong e-mail"
    except ValueError:
        print("Error decoding JSON response")
        return None
    if res_json["success"] == True:
        return res_json
    else:
        print("Error reseting password")
        print(res_json)
        return None
