import shipping_rate_functions

def initialize_cart(user_cart_session):
    user_cart_session['cart'] = {}
    user_cart_session['cart']['line_items'] = []
    user_cart_session['cart']['coupon_lines'] = []
    user_cart_session['cart']['coupon_message'] = ""
    user_cart_session['cart']['total_coupon_discount'] = 0.0
    return user_cart_session

def assign_line_item_price_total(item, variation, session):
    item["price"] = get_variation_price(variation)
    item["regular_price"] = float(variation["regular_price"])
    item["on_sale"] = variation["on_sale"]
    item["subtotal"] = str(item["regular_price"] * float(item["quantity"]))
    item["total"] = str(item["price"] * float(item["quantity"]))

def assign_cart_subtotal_shipping_total_lines(session):
    session["cart"]["subtotal"] = calculate_subtotal_cart(session["cart"]["line_items"])
    session["cart"]["shipping_total"] = calculate_delivery(session["cart"]["subtotal"])
    session["cart"]["total"] = session["cart"]["subtotal"] + session["cart"]["shipping_total"]
    session["cart"]["shipping_lines"] = add_shipping_lines(session["cart"]["shipping_total"])
    session.modified = True  # Mark the session as modified to ensure it gets saved

def calculate_subtotal_cart(line_items):
    return sum(float(item["total"]) for item in line_items)

# Change Price here for delivery 
def calculate_delivery(subtotal_order):
    if subtotal_order >= 30:
        return 0.0
    else:
        shipping_rate_str = shipping_rate_functions.get_shipping_rate()
        shipping_rate_float = float(shipping_rate_str)
        return shipping_rate_float

def add_shipping_lines(shipping_value):
    if shipping_value == 0.0:
        return [{
            "method_id": "free_shipping",
            "method_title": "Free shipping",
            "total": "0.00"
        }]
    else:
        return [{
            "method_id": "flat_rate",
            "method_title": "Flat rate",
            "total": f"{shipping_value}0"
        }]
    
def get_variation_price(variation):
    if variation["on_sale"]:
        return float(variation["sale_price"]) 
    else:
        return float(variation["regular_price"])

def reapply_coupons(user_cart_session):
    if "coupon_lines" in user_cart_session["cart"] and len(user_cart_session["cart"]["coupon_lines"]) > 0:
        total_discount = 0.0
        for coupon in user_cart_session["cart"]["coupon_lines"]:
            for item in user_cart_session["cart"]["line_items"]:
                total_discount += apply_coupon_on_item_and_calculate_discount(item, coupon, user_cart_session)
                total_discount = round(total_discount, 2)
        user_cart_session["cart"]["total_coupon_discount"] = total_discount
        user_cart_session["cart"]["coupon_message"] = "Code promo appliqué"
    else:
        user_cart_session["cart"]["total_coupon_discount"] = 0.0

def apply_coupon_on_item_and_calculate_discount(item, coupon, user_cart_session):
    original_price = float(item["price"])
    discounted_price = get_coupon_price_for_item(item, coupon, user_cart_session)
    item["price"] = discounted_price
    original_total = original_price * float(item["quantity"])
    discounted_total = discounted_price * float(item["quantity"])
    item["total"] = str(discounted_total)
    return original_total - discounted_total

def get_coupon_price_for_item(item, coupon, session):
    # Apply the coupon to line item
    discount_type = coupon["discount_type"]
    discount_amount = float(coupon["amount"])
    if discount_type == "percent":
        discount = item["price"] * (discount_amount / 100)
        return item["price"] - discount
    else:
        return item["price"]

def get_coupon_by_code(coupon_data, coupons_list):
    coupon_code = coupon_data.get("coupon_code")
    if not coupon_code:
        return None
    for coupon in coupons_list:
        if coupon["code"] == coupon_code:
            return coupon
    return None

def clean_coupons(coupons):
    return [
        {
            "code": coupon["code"],
            "amount": coupon["amount"],
            "discount_type": coupon["discount_type"],
            "status": coupon["status"]
        }
        for coupon in coupons
    ]
