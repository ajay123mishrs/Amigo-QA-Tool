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

            # Link kholna
            page.goto(test_url, timeout=60000)
            
            # 🔥 Yahan humne bot ko 7 second rukne ko kaha hai taaki redirect ho sake
            page.wait_for_load_state('networkidle', timeout=60000)
            page.wait_for_timeout(7000) 

            final_url = page.url
            browser.close()

            # 🔥 "undefined" hatane ke liye message add kiya
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
