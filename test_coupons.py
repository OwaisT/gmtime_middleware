import order_functions

# Define the base URL and authentication
base_url = "https://backend.owaisrb-one.com/wp-json/wc/v3/"
auth = ('consumer_key', 'consumer_secret')  # Replace with your actual credentials

order_data = {
    "billing": {
        "first_name": "John",
        "last_name": "Doe",
        "address_1": "969 Market",
        "address_2": "",
        "city": "San Francisco",
        "state": "CA",
        "postcode": "94103",
        "country": "US",
        "email": "" 
    },
    "customer_id": 1,
    "line_items": [
        {
            "variation_id" : 1,
            "quantity": 2,
            "color" : "blue"
        },
        {
            "variation_id": 2,
            "quantity": 1,
            "color" : "blue"
        }
    ],
    "shipping": {
        "first_name": "John",
        "last_name": "Doe",
        "address_1": "969 Market",
        "address_2": "",
        "city": "San Francisco",
        "state": "CA",
        "postcode": "94103",
        "country": "US"
    },
    "shipping_lines": [
        {
            "method_id": "flat_rate",
            "method_title": "Flat Rate",
            "total": "10.00"
        }
    ],
    "coupon_lines": [
        {
            "code": "10OFF"
        },
        {
            "code": "20OFF"
        }
    ]
}
# Call the get_coupons function
organized_order_data = order_functions.organize_order_data_for_creation(order_data)

print(organized_order_data["coupon_lines"])  # Output: [{'code': '10OFF'}, {'code': '20OFF'}]