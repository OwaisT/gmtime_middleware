import product_functions
import os
import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
import cart.utility_cart_functions as utility_cart_functions

load_dotenv()

# API credentials
consumer_key = os.environ.get("CONSUMER_KEY")
consumer_secret = os.environ.get("CONSUMER_SECRET")
base_url = os.environ.get("BASE_URL")

auth = HTTPBasicAuth(consumer_key, consumer_secret)

def add_to_cart(data, user_cart_session):
    if 'line_item' not in data:
        return {'error': 'Invalid data'}, 400
    line_item = data['line_item']
    if 'cart' not in user_cart_session:
        user_cart_session = utility_cart_functions.initialize_cart(user_cart_session)
    if "user_id" in data:
        user_cart_session['cart']['user_id'] = data['user_id']  # Set user_id in the cart
    # Check if item with the same variation_id exists
    item_exists = False
    variation_for_price = product_functions.get_variation(line_item["product_id"], line_item["variation_id"])
    for existing_item in user_cart_session['cart']["line_items"]:
        if existing_item['variation_id'] == line_item['variation_id']:
            # Update the existing item
            existing_item['quantity'] = line_item['quantity']
            utility_cart_functions.assign_line_item_price_total(existing_item, variation_for_price, user_cart_session)
            item_exists = True
            break
    if not item_exists:
        # Add the new item to the cart
        utility_cart_functions.assign_line_item_price_total(line_item, variation_for_price, user_cart_session)
        user_cart_session['cart']["line_items"].append(line_item)
    
    utility_cart_functions.reapply_coupons(user_cart_session)

    utility_cart_functions.assign_cart_subtotal_shipping_total_lines(user_cart_session)
    return user_cart_session['cart']

def remove_from_cart(user_cart_session, variation_id):
    if 'cart' in user_cart_session:
        user_cart_session['cart']['line_items'] = [item for item in user_cart_session['cart']['line_items'] if item['variation_id'] != variation_id]   
    utility_cart_functions.reapply_coupons(user_cart_session)
    utility_cart_functions.assign_cart_subtotal_shipping_total_lines(user_cart_session)
    return user_cart_session['cart']
    
def apply_coupon_on_cart(coupon_data, coupons_list, user_cart_session):
     # Check if the cart exists and has line items
    if "cart" not in user_cart_session or "line_items" not in user_cart_session["cart"] or len(user_cart_session["cart"]["line_items"]) == 0:
        user_cart_session["cart"]["coupon_message"] = "Le panier est vide ou n'existe pas"
        return user_cart_session["cart"], 200
    if 'coupon_code' not in coupon_data:
        user_cart_session["cart"]["coupon_message"] = "Code promo manquant ou invalide"
        return user_cart_session["cart"], 200
    coupon = utility_cart_functions.get_coupon_by_code(coupon_data, coupons_list)
    if coupon is None:
        user_cart_session['cart']['coupon_message'] = "Code promo non valide"
        return user_cart_session['cart'], 200
    if "coupon_lines" in user_cart_session["cart"]:
        for existing_coupon in user_cart_session["cart"]["coupon_lines"]:
            if existing_coupon["code"] == coupon["code"]:
                user_cart_session["cart"]["coupon_message"] = "Code déjà appliqué"
                return user_cart_session["cart"], 200

    total_discount = 0.0
    for item in user_cart_session["cart"]["line_items"]:
        total_discount += utility_cart_functions.apply_coupon_on_item_and_calculate_discount(item, coupon, user_cart_session)
        total_discount = round(total_discount, 2)
    
    utility_cart_functions.assign_cart_subtotal_shipping_total_lines(user_cart_session)
    user_cart_session['cart']['coupon_lines'].append(coupon)
    user_cart_session["cart"]["total_coupon_discount"] = total_discount
    user_cart_session["cart"]["coupon_message"] = "Code promo appliqué"
    return user_cart_session['cart']

def get_coupons():
    url = f"{base_url}coupons"
    response = requests.get(url, auth=auth)
    coupons = response.json()
    return utility_cart_functions.clean_coupons(coupons)
