from flask import Flask, session, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import product_functions
import mailer
import user_functions
import order_functions
import cart.cart_functions as cart_functions
import stripe
import headline_functions
import random

load_dotenv()

stripe.api_key = os.getenv("STRIPE_API_KEY")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY_SESSIONS")

# TODO: Remove localhost before deployment
CORS(app, supports_credentials=True, resources={r"/*": {"origins": ["https://gmtimestore.com", "https://www.gmtimestore.com", "https://gmtimestore.com/", "https://www.gmtimestore.com/", "http://localhost:3000", "http://localhost:3000"]}})

variations_for_products_page_homme = None
variations_for_products_page_femme = None
variations_for_products_page_fille = None
variations_for_products_page_garcon = None
variations_for_products_page_enfant = None
variations_for_products_page_autres = None
featured_products_variations = None
sale_products_variations = None
headline = None
window_products = None
coupons_list = None

def load_products():
    global variations_for_products_page_homme
    global variations_for_products_page_femme 
    global variations_for_products_page_fille
    global variations_for_products_page_garcon
    global variations_for_products_page_enfant
    global variations_for_products_page_autres
    global featured_products_variations
    global sale_products_variations
    global headline
    global window_products
    global coupons_list

    variations_for_products_page_homme = product_functions.get_products_variations(product_functions.get_products("16"), sale_products=False)
    variations_for_products_page_femme = product_functions.get_products_variations(product_functions.get_products("17"), sale_products=False)
    variations_for_products_page_fille = product_functions.get_products_variations(product_functions.get_products("19"), sale_products=False)
    variations_for_products_page_garcon = product_functions.get_products_variations(product_functions.get_products("18"), sale_products=False)
    variations_for_products_page_enfant = product_functions.get_products_variations(product_functions.get_products("20"), sale_products=False)
    variations_for_products_page_autres = product_functions.get_products_variations(product_functions.get_products("21"), sale_products=False)
    featured_products_variations = product_functions.get_products_variations(product_functions.get_featured_products(), sale_products=False)
    sale_products_variations = product_functions.get_products_variations(product_functions.get_featured_products(), sale_products=True)
    headline = headline_functions.get_headline()
    if len(featured_products_variations) > 7:
        window_list = random.sample(featured_products_variations, len(featured_products_variations))
        window_products = window_list[0:8]
    else:
        window_products = featured_products_variations
    coupons_list = cart_functions.get_coupons()

load_products()
print(coupons_list)

def authenticate(api_key):
    return api_key == app.config['API_KEY']

@app.route("/products_reload", methods=['GET'])
def products_reload():
    load_products()
    return "Data reloaded", 200

@app.route("/keep_alive", methods=["GET"])
def keep_alive():
    return "OK", 200

@app.route("/get_headline", methods=["GET"])
def get_headline():
    if headline != None:
        return headline, 200
    else:
        return "Error retrieving headline", 500

@app.route("/authenticate_user", methods=['POST'])
def authenticate_user():
    data = request.get_json()
    authentication = user_functions.authenticate_user(data)
    if authentication != None:
        return authentication, 200
    else:
        return "Email ou mot de passe incorrect", 400

@app.route("/get_user", methods=['POST'])
def get_user():
    data = request.get_json()
    token = data["user_token"]
    user = user_functions.get_user(token)
    if user != None:
        return user, 200
    else:
        return "Erreur lors de la récupération du compte", 400

@app.route("/create_user", methods=['POST'])
def create_user():
    data = request.get_json()
    new_user = user_functions.create_user(data)
    if new_user != None:
        return new_user, 200
    else:
        return "Erreur lors de la création du compte", 400

@app.route("/reset_pass", methods=["POST"])
def reset_password():
    data = request.get_json()
    reset_request = user_functions.reset_password(data)
    if reset_request != None:
        return reset_request, 200
    elif reset_request == "Wrong e-mail":
        return "Email incorrecte", 400
    else:
        return "Erreur lors de la réinitialisation du mot de passe", 400

@app.route("/create_order", methods=['POST'])
def create_order():
    data = request.get_json()
    new_order = order_functions.create_order(data)
    if new_order != None:
        return new_order, 200
    else:
        return "Error creating order", 400

@app.route('/payment', methods=['POST'])
def make_payment():
    data = request.get_json()
    order = order_functions.get_order(data["id"])
    if order["shipping"]["first_name"] == data["shipping"]["first_name"]:
        try:
            # Create a PaymentIntent with the order amount and currency
            intent = stripe.PaymentIntent.create(
                amount= order_functions.calculate_order_total_for_stripe(order["total"]),
                currency='eur',
                # In the latest version of the API, specifying the `automatic_payment_methods` parameter is optional because Stripe enables its functionality by default.
                automatic_payment_methods={
                    'enabled': True,
                }
            )
            return jsonify({'client_secret': intent['client_secret']}), 200
        except Exception as e:
            return jsonify(error=str(e)), 403
    else:
        return "Order name doesn't match", 400

@app.route("/get_orders", methods=["POST"])
def get_orders():
    data = request.get_json()
    orders = order_functions.get_orders(data["user_id"])
    print(data["user_id"])
    if orders != None:
        if len(orders) != 0:
            if orders[0]["billing"]["email"] == data["email"]:
                return orders, 200
            else:
                print("wront user identified")
                return "Request not allowed", 400
        else:
            return [], 200
    else:
        print("no orders retrived or found")
        return "Error getting orders", 400

@app.route("/get_order", methods=["POST"])
def get_order():
    data = request.get_json()
    order = order_functions.get_order(data["order_id"])
    if order != None:
        if order["customer_id"] == data["user_id"] and order["billing"]["email"] == data["email"]: 
            return order, 200
        else:
            return "Request not allowed", 400
    else:
        return "Error getting order", 400

@app.route("/confirm_order", methods=["POST"])
def confirm_order():
    data = request.get_json()
    order = order_functions.get_order(data["order_id"])
    if order["shipping"]["first_name"] == data["first_name"] and order["shipping"]["last_name"] == data["last_name"]:
        confirmation = order_functions.confirm_order(data["order_id"])
    else:
        return "Order names don't match", 400
    if confirmation != None:
        order = order_functions.get_order(data["order_id"])
        if order != None:
            return order, 200
        else:
            return "Error getting confirmed order", 400
    else:
        return "Error confirming order", 400

@app.route("/products", methods=['POST'])
def get_products():
    data = request.get_json()
    if data["category"] == "homme":
        if variations_for_products_page_homme != None:
            return variations_for_products_page_homme, 200
        else:
            "Error Retrieving products homme", 500
    elif data["category"] == "femme":
        if variations_for_products_page_femme != None:
            return variations_for_products_page_femme, 200
        else:
            "Error Retrieving products femme", 500
    elif data["category"] == "fille":
        if variations_for_products_page_fille != None:
            return variations_for_products_page_fille, 200
        else:
            "Error Retrieving products fille", 500
    elif data["category"] == "garcon":
        if variations_for_products_page_garcon != None:
            return variations_for_products_page_garcon, 200
        else:
            "Error Retrieving products garcon", 500
    elif data["category"] == "enfant":
        if variations_for_products_page_enfant != None:
            return variations_for_products_page_enfant, 200
        else:
            "Error Retrieving products enfant", 500
    elif data["category"] == "autres":
        if variations_for_products_page_autres != None:
            return variations_for_products_page_autres, 200
        else:
            "Error Retrieving products homme", 500
    else:
        return "Category not found", 400

@app.route("/sale_products", methods=['GET'])
def get_featured_products():
    if sale_products_variations != None:
        return sale_products_variations, 200
    else:
        "Error Retrieving sale products", 500

@app.route("/window_products", methods=['GET'])
def get_window_products():
    if window_products != None:
        return window_products, 200
    else:
        "Error Retrieving window products", 500

@app.route("/product/<path:subpath>", methods=['GET'])
def get_product(subpath=''):
    product = product_functions.get_product_and_variations(subpath)
    if product != None:
        return product, 200
    else:
        return "Error getting product", 400

@app.route("/variation_stock", methods=["POST"])
def get_variation_stock():
    data = request.get_json()
    stock = product_functions.get_variation_stock(data["product_id"], data["variation_id"])
    if stock != None:
        return stock, 200
    else:
        return "Error retrieving stock", 400

@app.route("/reviews/<path:subpath>", methods=["GET"])
def get_reviews(subpath=''):
    reviews = product_functions.get_product_reviews(subpath)
    if reviews == None:
        return "Error Retrieving Reviews", 400
    return reviews, 200

@app.route("/create_review", methods=["POST"])
def post_review():
    data = request.get_json()
    return product_functions.send_product_review(data)

@app.route('/send_email', methods=['POST'])
def send_email_route():
    data = request.get_json()
    mail = mailer.send_contact_email(data)
    if mail == 'Mail sent succesfully':
        return mail, 200
    else:
        return mail, 500

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    return cart_functions.add_to_cart(data, session)  # Return a JSON response

@app.route('/cart', methods=['GET'])
def get_cart():
    return session.get('cart', [])

@app.route('/remove_from_cart', methods=["POST"])
def remove_from_cart():
    data = request.get_json()
    return cart_functions.remove_from_cart(session, data["variation_id"]), 200

@app.route('/delete_cart', methods=["GET"])
def delete_cart():
    session.clear()
    return "Cart Cleared", 200

@app.route('/apply_coupon', methods=["POST"])
def apply_coupon():
    data = request.get_json()
    return cart_functions.apply_coupon_on_cart(data, coupons_list, session)

# TODO: Remove debug and port before deployment
if __name__ == "__main__":
    app.run(debug=True, port=5000)
