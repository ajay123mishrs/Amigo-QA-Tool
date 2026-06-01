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
    
    # Check and replace UID (case insensitive handling)
    if 'UID' in query:
        query['UID'] = [new_uid]
    elif 'uid' in query:
        query['uid'] = [new_uid]
        
    new_query = urlencode(query, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_test', methods=['POST'])
def run_test():
    try:
        data = request.json
        original_url = data.get('url', '')
        uid = data.get('uid', 'TEST1')
        country = data.get('country', 'US')

        test_url = replace_uid(original_url, uid)

        # Render/Cloud server ke liye special browser settings
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--single-process'
                ],
                proxy={
                    "server": f"http://{SERVER}",
                    "username": USERNAME,
                    "password": PASSWORD
                }
            )
            
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()

            # Survey link open karna aur load hone ka wait karna
            page.goto(test_url, timeout=60000)
            page.wait_for_load_state('load', timeout=60000)

            final_url = page.url
            browser.close()

            return jsonify({
                "status": "success",
                "final_url": final_url
            })

    except Exception as e:
        # 🔥 Yahan par humara Asli Error logs mein print hoga
        print(f"🔥 ASLI ERROR: {str(e)}", flush=True)
        return jsonify({
            "status": "error",
            "message": "Failed to load",
            "error_details": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
