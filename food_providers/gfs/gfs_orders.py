import requests
import json
import os

cookie = 'GCLB=CKLt1Mn576WjIRAD; EA_UID=c9727aed-fa47-4300-836b-b1e8350b7ae5; GOR=us-east1; XSRF-TOKEN=9c436546-d727-402c-8771-85017336959b; __Secure-GORDONORDERING2=MjNiN2MxNmItY2ZhMS00YWFiLTk2NzAtMjE1ZWMxNzJhNTA1; EA_SESSION_SAMPLED=true; EA_SID=b16d4300-1506-416e-8fc3-c0a10f696e9f; __Secure-GORDONORDERING2=M2E2NjZkYTAtZWU2MS00MmEzLWJjODktZDMwZjc4MDRmMDMz; GCLB=CJP2zOujmdCTqQEQAw; XSRF-TOKEN=c157d075-b971-4414-98e6-889f8db8fa92'

def extract_order_numbers(data):
    if isinstance(data, str):
        data = json.loads(data)
    
    return [order.get("orderNumber") for order in data.get("orders", []) if "orderNumber" in order]

def save_item_to_json(item_data, filename="gfs_items.json"):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = {}
    else:
        existing_data = {}

    item_code = item_data.get("itemCode")
    item_description = item_data.get("itemDescription")

    if item_code and item_code not in existing_data:
        existing_data[item_code] = item_description
        with open(filename, "w") as f:
            json.dump(existing_data, f, indent=4)
        return f"Item {item_code} added successfully."
    else:
        return f"Item {item_code} already exists or is missing item code."

def get_past_orders(cookie):
    url = "https://order.gfs.com/us-east1/api/v6/orders"
    payload = {}
    headers_one = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en_US',
    'dnt': '1',
    'priority': 'u=1, i',
    'referer': 'https://order.gfs.com/orders?activeTab=order-history',
    'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
    'x-logrocket-url': '',
    'x-requested-with': 'XMLHttpRequest',
    'x-xsrf-token': '9c436546-d727-402c-8771-85017336959b',
    'Cookie': cookie
    }

    response = requests.request("GET", url, headers=headers_one, data=payload)

    return extract_order_numbers(response.text)

def dump_item_to_json(material_num, cookie):
    url = f"https://order.gfs.com/api/v1/materials/{material_num}/nutrition"
    payload = {}
    headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9',
    'dnt': '1',
    'priority': 'u=1, i',
    'referer': f'https://order.gfs.com/product/{material_num}',
    'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
    'Cookie': cookie
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    save_item_to_json(response.text)

def retrive_order_information(order_num, cookie):
    url = "https://order.gfs.com/us-east1/api/v5/order-details"

    payload = json.dumps({
    "orderNumber": f"{order_num}",
    "orderType": "STORE_FULFILLMENT",
    "groupNumber": "01"
    })
    headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en_US',
    'content-type': 'application/json',
    'dnt': '1',
    'origin': 'https://order.gfs.com',
    'priority': 'u=1, i',
    'referer': f'https://order.gfs.com/orders/{order_num}/details/store_fulfillment/01',
    'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
    'x-logrocket-url': '',
    'x-requested-with': 'XMLHttpRequest',
    'x-xsrf-token': '9c436546-d727-402c-8771-85017336959b',
    'Cookie': cookie
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.text

def extract_material_numbers(data):
    if isinstance(data, str):
        data = json.loads(data)
    return [line.get("materialNumber") for line in data.get("orderLines", []) if "materialNumber" in line]


def get_all_ordered_materials(cookie):
    material_list = []
    for order_num in get_past_orders(cookie=cookie):
        material_list.extend(extract_material_numbers(retrive_order_information(order_num=order_num, cookie=cookie)))
    return set(material_list)


def get_gfs_cookie():
    """
    Opens Chromium to GFS login page, lets you authenticate, then extracts cookies
    for order.gfs.com and returns them as a Cookie: header string.
    Requires: pip install playwright ; python -m playwright install chromium
    """
    from playwright.sync_api import sync_playwright

    domain_filter = "order.gfs.com"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://order.gfs.com/home")

        print("Log in via the opened browser, then press Enter here...")
        input()

        cookies = context.cookies()
        cookie_header = "; ".join(
            f"{c['name']}={c['value']}" for c in cookies if domain_filter in c.get("domain", "")
        )

        browser.close()
        return cookie_header


# print(get_all_ordered_materials(cookie=cookie))
print(get_gfs_cookie())