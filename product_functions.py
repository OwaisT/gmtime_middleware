import os
import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

# API credentials
consumer_key = os.environ.get("CONSUMER_KEY")
consumer_secret = os.environ.get("CONSUMER_SECRET")
base_url = os.environ.get("BASE_URL")

auth = HTTPBasicAuth(consumer_key, consumer_secret)

# Gets the products from backend for products page,
# will be called in get_products_variations() function to then receive its variations
def get_products(category_id):
    all_products = []
    url = f"{base_url}products?category={category_id}&page=1&per_page=50"
    response = requests.get(url, auth=auth)
    if response.status_code == 200:
        products = response.json()
        for product in products:
            if product["status"] == "publish":
                all_products.append(product)
    else:
        print(f"Error fetching products: {response.status_code}")
    return all_products

# Same as get_products() but fetches featured products
def get_featured_products():
    all_products = []
    url = base_url + "products?featured=true"
    response = requests.get(url, auth=auth)
    if response.status_code == 200:
        products = response.json()
        for product in products:
            if product["status"] == "publish":
                all_products.append(product)
    else:
        print(f"Error fetching featured products: {response.status_code}")
    return all_products

# Fetches variations of the products to then render on products page,
# will be called in app.py and will take get_products() as input
def get_products_variations(products_list, sale_products):
    all_variations = []
    for product in products_list:
        whole_product_variations = fetch_product_variations_from_api(product)
        all_variations.extend(whole_product_variations)
    if sale_products:
        organized_variations = organize_sale_variations(all_variations)
    else:
        organized_variations = organize_variations(all_variations)
    return organized_variations

# organize variations with products acording to attributes
def fetch_product_variations_from_api(product):
    color_attribute = None
    for attribute in product.get("attributes"):
        if attribute.get("name") == "Color":
            color_attribute = attribute
            break
    num_color_options = len(color_attribute["options"])
    print(f"Number of color options for {product['name']}: {num_color_options}")
    per_page_value_calculation = num_color_options * 5
    variations = make_api_call_variations(product["id"], per_page_value_calculation)
    colored_variations = select_colored_variations(variations)
    whole_product_variations = add_whole_product_to_variation(product, colored_variations)
    return whole_product_variations

# Get variations for a product from backend
def make_api_call_variations(product_id, per_page_value):
    url = base_url + 'products/' + str(product_id) + "/variations?per_page=" + str(per_page_value)
    response = requests.get(url, auth=auth)
    return response.json()

# Organize colors of a product for variations swatches
def select_colored_variations(variations):
    product_colors = ["idle"]
    colored_variations = []
    for variation in variations:
        variation_color = get_variation_color(variation)
        if variation_color not in product_colors:
            product_colors.append(variation_color)
            colored_variations.append(variation)
    product_colors.remove("idle")
    for colored_variation in colored_variations:
        colored_variation["swatches"] = product_colors
    return colored_variations

# Get the color's text for variation
def get_variation_color(variation):
    for attribute in variation.get("attributes"):
        if attribute.get("name") == "Color":
            color_options = attribute
            variation_color = color_options["option"]
            break
        else:
            variation_color = ""
    return variation_color

# Adds the product to variation
def add_whole_product_to_variation(product, variations):
    whole_product_variations = []
    for variation in variations:
        variation["whole_product"] = product
        whole_product_variations.append(variation)
    return whole_product_variations

# organize_variations to remove unnecessary data
def organize_variations(variations):
    organized_variations = []
    for variation in variations:
        organized_variation = organize_variation(variation)
        organized_variations.append(organized_variation)        
    return organized_variations

# Same as organize_variations but checks if the variation is on sale or not
def organize_sale_variations(variations):
    organized_variations = []
    for variation in variations:
        if variation["sale_price"] != "":
            organized_variation = organize_variation(variation)
            organized_variations.append(organized_variation)
    return organized_variations

# organize one single variation and called in organize_variations or organize_sale_variations
def organize_variation(variation):
    organized_variation = {}
    organized_variation["color"] = get_variation_color(variation)
    organized_variation["name"] = variation["whole_product"]["name"]
    organized_variation["categories"] = variation["whole_product"]["categories"]
    organized_variation["sizes"] = get_variation_sizes(variation)
    organized_variation["stock_availability"] = variation["whole_product"]["stock_status"]
    organized_variation["on_sale"] = variation["on_sale"]
    organized_variation["regular_price"] = variation["regular_price"]
    organized_variation["sale_price"] = variation["sale_price"]
    organized_variation["price"] = variation["price"]
    organized_variation["swatches"] = variation["swatches"]
    organized_variation["image"] = variation["image"]
    organized_variation["unique_id_variation"] = variation["id"]
    organized_variation["status"] = variation["whole_product"]["status"]
    organized_variation["unique_id_product"] = variation["whole_product"]["id"]
    organized_variation["product_slug"] = variation["whole_product"]["slug"]
    return organized_variation

# Gets the sizes from product for adding in variations
def get_variation_sizes(variation):
    for attribute in variation["whole_product"]["attributes"]:
        if attribute.get("name") == "Size":
            size_options = attribute
            variation_sizes = size_options["options"]
            break
        else:
            variation_sizes = ""
    return variation_sizes

# get product and its variation along with organizing to send to frontend
def get_product_and_variations(product_id):
    url = f"{base_url}products/{product_id}"
    response = requests.get(url, auth=auth)
    if response.status_code == 200:
        fetched_product = response.json()
        product = organize_product_for_product_page(whole_product=fetched_product)
        for attribute in product.get("attributes"):
            if attribute.get("name") == "Color":
                color_attribute = attribute
                break
        num_color_options = len(color_attribute["options"])
        print(f"Number of color options for {product['name']}: {num_color_options}")
        per_page_value_calculation = num_color_options * 5
        variation_url = f"{url}/variations?per_page={per_page_value_calculation}"
        variations_response = requests.get(url=variation_url, auth=auth)
        if variations_response.status_code == 200:
            fetched_variations = variations_response.json()
            product["fetched_variations"] = organize_variations_for_product_page(fetched_variations)
            return product
        else:
            print("Error getting variations")
            print(variations_response.json())
            return None
    else:
        print("Error getting product")
        print(response.json())
        return None
    
# Get one single product's variations for page of the product
def get_product_variations(product):
    url = base_url + 'products/' + str(product["id"]) + "/variations?per_page=30"
    response = requests.get(url, auth=auth)
    product["all_variations"] = response.json()
    return product

# Organize product for its page to remove unnecessary data
def organize_product_for_product_page(whole_product):
    product = {}
    product["attributes"] = whole_product["attributes"]
    product["average_rating"] = whole_product["average_rating"]
    product["description"] = whole_product["description"]
    product["dimensions"] = whole_product["dimensions"]
    product["id"] = whole_product["id"]
    product["images"] = whole_product["images"]
    product["name"] = whole_product["name"]
    product["short_description"] = whole_product["short_description"]
    product["weight"] = whole_product["weight"]
    return product

# Organize variations for product page to remove unnecessary data
def organize_variations_for_product_page(whole_variations):
    variations = []
    for whole_variation in whole_variations:
        variation = {}
        variation["attributes"] = whole_variation["attributes"]
        variation["id"] = whole_variation["id"]
        variation["image"] = whole_variation["image"]
        variation["name"] = whole_variation["name"]
        variation["on_sale"] = whole_variation["on_sale"]
        variation["price"] = whole_variation["price"]
        variation["regular_price"] = whole_variation["regular_price"]
        variation["sale_price"] = whole_variation["sale_price"]
        variation["stock_quantity"] = whole_variation["stock_quantity"]
        variations.append(variation)
    return variations

# Get product reviews from backend
def get_product_reviews(product_id):
    url = f"{base_url}products/reviews"
    response = requests.get(url, auth=auth, params={ 'product': product_id })
    if response.status_code == 200:
        return response.json()
    else:
        print("Error retrieving reviews")
        print(response.json)
        return None

# Send product review to backend
def send_product_review(review):
    url = f"{base_url}products/reviews"
    response = requests.post(url, auth=auth, json=review)
    if response.status_code == 201:
        return response.json()
    else:
        print("Error posting review")
        print(response.json)
        return None

# Get stock for variation
def get_variation_stock(product_id, variation_id):
    url = f"{base_url}products/{product_id}/variations/{variation_id}"
    response = requests.get(url, auth=auth)
    if response.status_code == 200:
        res_json = response.json()
        return str(res_json["stock_quantity"])
    else:
        print("Error getting stock")
        print(response.json)
        return None

# Gets variation for getting it's price in cart and cart
def get_variation(product_id, variation_id):
    url = f"{base_url}products/{product_id}/variations/{variation_id}"
    response = requests.get(url, auth=auth)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error getting variation")
        print(response.json)
        return None
