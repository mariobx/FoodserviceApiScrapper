import requests
import json
import os
from playwright.sync_api import sync_playwright
from pathlib import Path
from http.cookies import SimpleCookie


COOKIE_PATH = Path("../cookies/gfs_cookie.txt")

def pretty_print_json(data):
    print(json.dumps(data, indent=4))

def extract_order_numbers(data):
    if isinstance(data, str):
        data = json.loads(data)
    
    return [order.get("orderNumber") for order in data.get("orders", []) if "orderNumber" in order]

def get_past_orders(cookies: SimpleCookie | str, timeout: float = 8.0):
    # Build Cookie header + XSRF from either SimpleCookie or raw string
    if isinstance(cookies, SimpleCookie):
        raw_cookie = "; ".join(f"{m.key}={m.value}" for m in cookies.values())
        xsrf = cookies["XSRF-TOKEN"].value if "XSRF-TOKEN" in cookies else None
    else:
        raw_cookie = cookies.strip()
        xsrf = None
        if "XSRF-TOKEN=" in raw_cookie:
            xsrf = raw_cookie.split("XSRF-TOKEN=", 1)[1].split(";", 1)[0]

    headers = {
        "accept": "application/json, text/plain, */*",
        "referer": "https://order.gfs.com/orders?activeTab=order-history",
        "user-agent": "Mozilla/5.0",
        "x-requested-with": "XMLHttpRequest",
        "Cookie": raw_cookie,
    }
    if xsrf:
        headers["x-xsrf-token"] = xsrf

    resp = requests.get(
        "https://order.gfs.com/us-east1/api/v6/orders",
        headers=headers,
        timeout=timeout,
        allow_redirects=False,
    )

    return extract_order_numbers(resp.text)


def retrieve_order_information(order_num: str, cookies: SimpleCookie | str, timeout: float = 8.0):
    url = "https://order.gfs.com/us-east1/api/v5/order-details"

    payload = json.dumps({
        "orderNumber": order_num,
        "orderType": "STORE_FULFILLMENT",
        "groupNumber": "01"
    })

    # Build Cookie header + XSRF
    if isinstance(cookies, SimpleCookie):
        raw_cookie = "; ".join(f"{m.key}={m.value}" for m in cookies.values())
        xsrf = cookies["XSRF-TOKEN"].value if "XSRF-TOKEN" in cookies else None
    else:
        raw_cookie = cookies.strip()
        xsrf = None
        if "XSRF-TOKEN=" in raw_cookie:
            xsrf = raw_cookie.split("XSRF-TOKEN=", 1)[1].split(";", 1)[0]

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en_US",
        "content-type": "application/json",
        "origin": "https://order.gfs.com",
        "referer": f"https://order.gfs.com/orders/{order_num}/details/store_fulfillment/01",
        "user-agent": "Mozilla/5.0",
        "x-requested-with": "XMLHttpRequest",
        "Cookie": raw_cookie,
    }
    if xsrf:
        headers["x-xsrf-token"] = xsrf

    response = requests.post(url, headers=headers, data=payload, timeout=timeout, allow_redirects=False)
    try:
        return response.json()
    except ValueError:
        return response.text
    
def extract_material_numbers(data):
    if isinstance(data, str):
        data = json.loads(data)
    return [line.get("materialNumber") for line in data.get("orderLines", []) if "materialNumber" in line]


def get_all_ordered_materials(cookie):
    material_list = []
    for order_num in get_past_orders(cookies=cookie):
        material_list.extend(extract_material_numbers(retrieve_order_information(order_num=order_num, cookies=cookie)))
    return set(material_list)


def get_gfs_cookie():
    """
    Launches Chromium, waits for the app to be logged-in (View Order visible),
    then returns:
      - raw_cookie: one-line Cookie header string
      - sc: SimpleCookie parsed object
    """
    NEEDED = {
    "__Secure-GORDONORDERING2",
    "XSRF-TOKEN",
    "GOR",
    "GCLB",
    "EA_UID",
    "EA_SESSION_SAMPLED",
    }
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context()
        page = ctx.new_page()

        page.goto("https://order.gfs.com/home")
        page.wait_for_selector('div[title="View Order"]', state="visible", timeout=0)

        # Only cookies for order.gfs.com
        ck = ctx.cookies(["https://order.gfs.com"])

        # Build a minimal Cookie header string
        parts = [f"{c['name']}={c['value']}" for c in ck if c["name"] in NEEDED]
        raw_cookie = "; ".join(parts)

        browser.close()

    sc = SimpleCookie()
    sc.load(raw_cookie)   # parse to dict-like object
    return raw_cookie, sc

def save_cookie(cookie: str, path: str) -> None:
    """
    Save the cookie string to a one-line text file.
    Overwrites if the file already exists.
    """
    Path(path).write_text(cookie.strip() + "\n", encoding="utf-8")

def read_cookie(path: str):
    """
    Read and return the contents of a one-line text file as a string.
    Strips trailing newline characters.
    """
    raw = Path(path).read_text(encoding="utf-8").strip()
    sc = SimpleCookie()
    sc.load(raw)
    return sc


def check_cookie_via_recommendations(sc: SimpleCookie, timeout: float = 8.0) -> bool:
    """
    Validate session by hitting a read-only JSON endpoint.
    Hardcoded: materialNumber=329401.
    """
    raw_cookie = "; ".join(f"{m.key}={m.value}" for m in sc.values())
    xsrf = sc["XSRF-TOKEN"].value if "XSRF-TOKEN" in sc else None

    url = "https://order.gfs.com/us-east1/api/v2/recommendations?page=pdp&materialNumber=329401"
    headers = {
        "accept": "application/json, text/plain, */*",
        "referer": "https://order.gfs.com/product/329401",
        "user-agent": "Mozilla/5.0",
        "x-requested-with": "XMLHttpRequest",
        "Cookie": raw_cookie,
    }
    if xsrf:
        headers["x-xsrf-token"] = xsrf

    try:
        r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=False)
    except requests.RequestException:
        return False

    if r.headers.get("login-location"):
        return False
    if 300 <= r.status_code < 400:
        loc = r.headers.get("Location", "")
        if "login" in loc or "sso.gfs.com" in loc:
            return False
    if r.status_code in (401, 403):
        return False

    ctype = (r.headers.get("Content-Type") or "").lower()
    return r.status_code == 200 and "json" in ctype

def dump_item_to_json(material_num: str, cookies: SimpleCookie | str, filename: str = "gfs_items.json", timeout: float = 8.0):
    url = f"https://order.gfs.com/api/v1/materials/{material_num}/nutrition"

    # Build Cookie header (+ optional XSRF if present)
    if isinstance(cookies, SimpleCookie):
        raw_cookie = "; ".join(f"{m.key}={m.value}" for m in cookies.values())
        xsrf = cookies["XSRF-TOKEN"].value if "XSRF-TOKEN" in cookies else None
    else:
        raw_cookie = cookies.strip()
        xsrf = None
        if "XSRF-TOKEN=" in raw_cookie:
            xsrf = raw_cookie.split("XSRF-TOKEN=", 1)[1].split(";", 1)[0]

    headers = {
        "accept": "application/json, text/plain, */*",
        "referer": f"https://order.gfs.com/product/{material_num}",
        "user-agent": "Mozilla/5.0",
        "Cookie": raw_cookie,
    }
    if xsrf:
        headers["x-xsrf-token"] = xsrf

    r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=False)
    r.raise_for_status()
    data = r.json()
    return save_item_to_json(data, filename=filename)

def save_item_to_json(item_data: dict, filename: str = "gfs_items.json"):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
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
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=4, ensure_ascii=False)
        return f"Item {item_code} added successfully."
    else:
        return f"Item {item_code} already exists or is missing item code."
    
def grab_correct_cookie(sc: SimpleCookie, timeout: float = 8.0):
    """
    If `sc` is valid (checked via recommendations endpoint), return it.
    Otherwise, fetch a fresh cookie via get_gfs_cookie(), verify it, save it, and return it.
    Raises if a valid cookie cannot be obtained.
    """
    if check_cookie_via_recommendations(sc):
        return sc

    raw_cookie, new_sc = get_gfs_cookie()
    if not check_cookie_via_recommendations(new_sc):
        raise RuntimeError("Failed to obtain a valid authenticated cookie.")

    save_cookie(raw_cookie, COOKIE_PATH)


grab_correct_cookie(read_cookie(COOKIE_PATH))
pretty_print_json(retrieve_order_information(get_past_orders(read_cookie(COOKIE_PATH))[1], read_cookie(COOKIE_PATH)))
