from flask import Flask, render_template, request, jsonify
from playwright.sync_api import sync_playwright
import string
import random
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

app = Flask(__name__)

# === GEONODE PROXY DETAILS ===
USERNAME = "geonode_fAijfEzx53"
PASSWORD = "6d4cd6c0-2695-4be7-9e54-4c270aeef7b8"
SERVER = "92.204.173.145:10000"

def replace_uid(url: str, new_uid: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    if 'UID' in query: query['UID'] = [new_uid]
    elif 'uid' in query: query['uid'] = [new_uid]
    else: query['UID'] = [new_uid]
    new_query = urlencode(query, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

@app.route('/')
def home():
    # Yeh aapki index.html web page ko load karega
    return render_template('index.html')

@app.route('/run_test', methods=['POST'])
def run_test():
    data = request.json
    survey_link = data.get('link')
    country_code = data.get('country', 'US').lower()
    uid = data.get('uid', 'TEST1')

    test_link = replace_uid(survey_link, uid)
    random_session = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    
    dynamic_username = f"{USERNAME}-type-residential-country-{country_code}-lifetime-1440-session-{random_session}"
    proxy_server_url = f"http://{SERVER}"

    result = {
        "status": "error",
        "message": "Something went wrong.",
        "final_url": ""
    }

    try:
        with sync_playwright() as playwright:
            # Server par screen nahi hoti isliye headless=True zaroori hai
            browser = playwright.chromium.launch(
                headless=True, 
                proxy={
                    "server": proxy_server_url,
                    "username": dynamic_username,
                    "password": PASSWORD
                }
            )
            context = browser.new_context()
            page = context.new_page()

            page.goto(test_link, timeout=90000, wait_until="domcontentloaded")
            
            # Start Survey button dhoondhna
            start_btn = page.locator("button:has-text('Start Survey'), a:has-text('Start Survey'), button:has-text('start survey')").first
            try:
                start_btn.wait_for(state="visible", timeout=20000)
                start_btn.click()
            except Exception:
                pass # Agar button nahi mila, toh sayad auto-redirect ho

            # Client page ka wait karna (60 seconds tak)
            page.wait_for_load_state("domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000) # Thoda extra buffer redirect ke liye
            
            final_url = page.url
            result["final_url"] = final_url
            result["status"] = "success"

            # URL dekh kar status batana
            if "quotafull" in final_url.lower():
                result["message"] = "Quota Full (QF) Reached!"
            elif "terminate" in final_url.lower() or "rejection" in final_url.lower():
                result["message"] = "Terminated (SO) Reached!"
            elif "complete" in final_url.lower() or "success" in final_url.lower():
                result["message"] = "Complete (C) Reached!"
            else:
                result["message"] = "Reached Client Page Successfully."

            browser.close()
            
    except Exception as e:
        result["message"] = str(e)

    return jsonify(result)

if __name__ == "__main__":
    # host='0.0.0.0' ka matlab hai aap ise apne mobile/WiFi network par khol sakte hain
    app.run(host='0.0.0.0', port=5000)