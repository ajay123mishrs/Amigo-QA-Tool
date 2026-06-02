from flask import Flask, render_template, request, jsonify
from playwright.sync_api import sync_playwright
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
    
    if 'UID' in query: query['UID'] = [new_uid]
    elif 'uid' in query: query['uid'] = [new_uid]
    else: query['UID'] = [new_uid]
        
    new_query = urlencode(query, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_test', methods=['POST'])
def run_test():
    try:
        data = request.json or request.form.to_dict() or {}
        original_url = data.get('link') or data.get('url') or ''
        uid = data.get('uid') or 'TEST1'

        if not original_url:
            raise Exception("Link nahi mila.")
        if not original_url.startswith('http'):
            original_url = 'https://' + original_url

        test_url = replace_uid(original_url, uid)
        print(f"🔥 YEH LINK KHOLEGA: {test_url}", flush=True)

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--single-process',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-gpu' # RAM bachane ke liye
                ],
                proxy={"server": f"http://{SERVER}", "username": USERNAME, "password": PASSWORD}
            )
            
            context = browser.new_context(
                ignore_https_errors=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # 🔥 RAM AUR TIME BACHANE KI NINJA TECHNIQUE: Images/CSS Block karna
            def block_heavy_resources(route):
                if route.request.resource_type in ["image", "media", "font", "stylesheet"]:
                    route.abort()
                else:
                    route.continue_()
            
            page.route("**/*", block_heavy_resources)

            # Fast loading ke sath page goto
            page.goto(test_url, timeout=90000, wait_until='domcontentloaded')
            page.wait_for_timeout(3000)
            
            # 🔥 SMART AUTO-CLICKER
            try:
                page.evaluate('''() => {
                    const buttons = Array.from(document.querySelectorAll('button, a, input'));
                    const startBtn = buttons.find(b => b.textContent.toLowerCase().includes('start') || b.value?.toLowerCase().includes('start') || b.textContent.toLowerCase().includes('begin') || b.textContent.toLowerCase().includes('next'));
                    if(startBtn) startBtn.click();
                }''')
                print("🔥 Auto-click executed!", flush=True)
            except Exception as e:
                print("🔥 Auto-click failed or button not found.", flush=True)

            # Redirect aur QF/COM URL pakadne ka wait
            page.wait_for_timeout(15000) 

            final_url = page.url
            browser.close()

            return jsonify({
                "status": "success",
                "message": "QA Test with Proxy & Auto-Click Done!", 
                "final_url": final_url
            })

    except Exception as e:
        return jsonify({"status": "error", "message": "Failed to load", "error_details": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
