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
    else:
        query['UID'] = [new_uid]
        
    new_query = urlencode(query, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_test', methods=['POST'])
def run_test():
    try:
        data = request.json or request.form.to_dict() or {}
        original_url = data.get('url') or data.get('survey_url') or data.get('surveyLink') or data.get('link') or ''
        uid = data.get('uid') or data.get('test_uid') or data.get('testUid') or 'TEST1'

        if not original_url:
            raise Exception("Link frontend se nahi aaya.")

        if not original_url.startswith('http'):
            original_url = 'https://' + original_url

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
                    '--disable-blink-features=AutomationControlled'
                ],
                proxy={
                    "server": f"http://{SERVER}",
                    "username": USERNAME,
                    "password": PASSWORD
                }
            )
            
            context = browser.new_context(
                ignore_https_errors=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # Page load karega (Fast)
            page.goto(test_url, timeout=90000, wait_until='domcontentloaded')
            page.wait_for_timeout(3000) # Page set hone ka wait
            
            # 🔥 NAYA FIX: AUTO-CLICK "START SURVEY"
            try:
                print("🔥 Start Survey button dhoondh raha hoon...", flush=True)
                page.evaluate('''() => {
                    const buttons = Array.from(document.querySelectorAll('button, a, input'));
                    const startBtn = buttons.find(b => b.textContent.toLowerCase().includes('start') || b.value?.toLowerCase().includes('start'));
                    if(startBtn) startBtn.click();
                }''')
            except Exception as e:
                print("🔥 Auto-click script error (ya button nahi mila)", flush=True)

            # Client URL (QF/COM) tak pahunchne ke liye solid 15 sec wait
            print("🔥 Redirect ka wait kar raha hoon...", flush=True)
            page.wait_for_timeout(15000) 

            final_url = page.url
            browser.close()

            return jsonify({
                "status": "success",
                "message": "Real QA Test Completed!", 
                "final_url": final_url
            })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Server Error Occurred",
            "error_details": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
