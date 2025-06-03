import os
import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

consumer_key = os.environ.get("CONSUMER_KEY")
consumer_secret = os.environ.get("CONSUMER_SECRET")
base_url = os.environ.get("BASE_URL")

auth = HTTPBasicAuth(consumer_key, consumer_secret)

def create_order(data):
    order_data = organize_order_data_for_creation(data)
    url = f"{base_url}orders"
    response = requests.post(url, auth=auth, json=order_data)
    res_json = response.json()
    if response.status_code == 201:
        update_user_info(res_json)
        return organize_order_for_creation(res_json)
    else:
        print("Error creating order")
        print(res_json)
        return None

def organize_order_data_for_creation(data):
    order_data = {}
    order_data["billing"] = data["billing"]
    order_data["customer_id"] = data["customer_id"]
    order_data["line_items"] = organize_line_items_for_order_creation(data["line_items"])
    order_data["shipping"] = data["shipping"]
    order_data["shipping_lines"] = data["shipping_lines"]
    order_data["coupon_lines"] = [{ "code" : item["code"] } for item in data["coupon_lines"] if item["discount_type"] == "percent"]
    return order_data

def organize_line_items_for_order_creation(line_items):
    items = []
    for line_item in line_items:
        item = {}
        item["product_id"] = line_item["variation_id"]
        item["quantity"] = line_item["quantity"]
        items.append(item)
    return items

def organize_order_for_creation(whole_order):
    order = {}
    order["id"] = whole_order["id"]
    order["shipping"] = whole_order["shipping"]
    order["billing"] = whole_order["billing"]
    return order

def update_user_info(order):
    customer_id = order["customer_id"]
    billing_info = order["billing"]
    if customer_id != 0:
        url = f"{base_url}customers/{customer_id}"
        user_billing = {
            "billing" : {
                "first_name": billing_info.get('first_name', ''),
                "last_name": billing_info.get('last_name', ''),
                "company": billing_info.get('company', ''),
                "address_1": billing_info.get('address_1', ''),
                "address_2": billing_info.get('address_2', ''),
                "city": billing_info.get('city', ''),
                "state": billing_info.get('state', ''),
                "postcode": billing_info.get('postcode', ''),
                "country": billing_info.get('country', ''),
                "email": billing_info.get('email', ''),
                "phone": billing_info.get('phone', '')
            }
        }
        response = requests.put(url, auth=auth, json=user_billing)
        if response.status_code == 200:
            print("User billing information updated successfully.")
        else:
            print(f"Failed to update user billing information. Status code: {response.status_code}")
    else:
        print("No user id in order")

def get_orders(user_id):
    url = f"{base_url}orders?customer={user_id}"
    response = requests.get(url, auth=auth)
    if response.status_code == 200:
        res_json = response.json()
        return organize_orders_for_page(res_json)
    else:
        return None

def organize_orders_for_page(whole_orders):
    orders = []
    for whole_order in whole_orders:
        order = {}
        order["date_created"] = whole_order["date_created"]
        order["id"] = whole_order["id"]
        order["status"] = whole_order["status"]
        order["total"] = whole_order["total"]
        order["billing"] = whole_order["billing"]
        orders.append(order)
    return orders

def get_order(order_id):
    url = f"{base_url}orders/{order_id}"
    response = requests.get(url, auth=auth)
    if response.status_code == 200:
        res_json = response.json()
        return organize_order_for_order_page(res_json)
    else:
        return None

def organize_order_for_order_page(whole_order):
    order = {}
    order["billing"] = whole_order["billing"]
    order["customer_id"] = whole_order["customer_id"]
    order["date_created"] = whole_order["date_created"]
    order["id"] = whole_order["id"]
    order["line_items"] = whole_order["line_items"]
    order["number"] = whole_order["number"]
    order["shipping"] = whole_order["shipping"]
    order["shipping_lines"] = whole_order["shipping_lines"]
    order["shipping_total"] = whole_order["shipping_total"]
    order["status"] = whole_order["status"]
    order["total"] = whole_order["total"]
    return order

# Change price here for delivery
def calculate_order_total_for_stripe(total):
    order_total = float(total)
    order_total = order_total * 100
    order_total = int(order_total)
    return order_total

def confirm_order(order_id):
    url = f"{base_url}orders/{order_id}"
    data = {"status" : "processing"}
    response = requests.put(url, auth=auth, json=data)
     # Check for successful response
    if response.status_code == 200:
        print(f"Order {order_id} status updated to processing")
        return "Order confirmed"
    else:
        # Handle errors (e.g., invalid order ID, unauthorized access)
        print(f"Error updating order: {response.text}")
        return None
