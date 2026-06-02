from flask import Flask, render_template, request, jsonify
from playwright.sync_api import sync_playwright
import string
import random
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import time

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
        # JSON ya Form data dono catch karega
        data = request.json or request.form.to_dict() or {}
        print(f"🔥 FRONTEND SE YEH DATA AAYA: {data}", flush=True)

        original_url = data.get('url') or data.get('survey_url') or data.get('surveyLink') or data.get('link') or ''
        uid = data.get('uid') or data.get('test_uid') or data.get('testUid') or 'TEST1'
        country = data.get('country') or data.get('countryCode') or 'US'

        if not original_url:
            raise Exception("Link frontend se backend tak nahi pahuncha. Variable name check karein!")

        test_url = replace_uid(original_url, uid)
        print(f"🔥 CHROME YEH LINK KHOLEGA: {test_url}", flush=True)

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--single-process',
                    '--disable-blink-features=AutomationControlled' # Bot detection strict bypass
                ],
                proxy={
                    "server": f"http://{SERVER}",
                    "username": USERNAME,
                    "password": PASSWORD
                }
            )
            
            # Asli Windows aur Chrome ka Mask
            context = browser.new_context(
                ignore_https_errors=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()

            # Webdriver identity hide karne ki script
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # Link kholna
            page.goto(test_url, timeout=60000)
            
            # Client server par exact redirect ke liye 8 second ka solid wait
            page.wait_for_timeout(8000) 

            final_url = page.url
            browser.close()

            return jsonify({
                "status": "success",
                "message": "Test Completed Successfully!", 
                "final_url": final_url
            })

    except Exception as e:
        print(f"🔥 ASLI ERROR: {str(e)}", flush=True)
        return jsonify({
            "status": "error",
            "message": "Failed to load",
            "error_details": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
