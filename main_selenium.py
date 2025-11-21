import time
import random
import os
import threading
import http.server
import socketserver
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Server is Running")
    
    def log_message(self, format, *args):
        pass

def execute_server():
    PORT = int(os.getenv('PORT', 4000))
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        httpd.serve_forever()

def setup_driver():
    print("[+] Setting up Chrome browser...")
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        import subprocess
        chromedriver_path = subprocess.check_output(['which', 'chromedriver']).decode().strip()
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("[+] Browser setup successful")
        return driver
    except Exception as e:
        print(f"[ERROR] Failed to setup browser: {str(e)}")
        raise

def load_cookies_to_browser(driver):
    print("[+] Loading cookies into browser...")
    try:
        with open('cookies.txt', 'r') as file:
            cookies_content = file.read().strip().strip('[]')
            
        driver.get('https://www.facebook.com')
        time.sleep(2)
        
        cookie_pairs = cookies_content.split(';')
        for pair in cookie_pairs:
            pair = pair.strip()
            if '=' in pair:
                key, value = pair.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                try:
                    cookie_dict = {
                        'name': key,
                        'value': value,
                        'domain': '.facebook.com'
                    }
                    driver.add_cookie(cookie_dict)
                except Exception as e:
                    print(f"[DEBUG] Could not add cookie {key}: {str(e)}")
        
        print("[+] Cookies loaded successfully")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to load cookies: {str(e)}")
        return False

def send_message_selenium(driver, convo_id, message):
    try:
        url = f'https://m.facebook.com/messages/thread/{convo_id}'
        print(f"[DEBUG] Navigating to mobile messenger: {url}")
        driver.get(url)
        time.sleep(5)
        
        print(f"[DEBUG] Current URL: {driver.current_url}")
        print(f"[DEBUG] Page title: {driver.title}")
        
        if "login" in driver.current_url.lower() or "login" in driver.title.lower():
            print("[ERROR] Not logged in! Cookies might be expired.")
            try:
                driver.save_screenshot('debug_login_page.png')
                print("[DEBUG] Screenshot saved: debug_login_page.png")
            except:
                pass
            return False
        
        wait = WebDriverWait(driver, 10)
        
        print("[DEBUG] Waiting for message box...")
        message_box_selectors = [
            "textarea[name='body']",
            "textarea#composerInput",
            "div[contenteditable='true']",
            "textarea",
            "input[type='text']"
        ]
        
        message_box = None
        for selector in message_box_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    if elem.is_displayed():
                        message_box = elem
                        print(f"[DEBUG] Found message box with selector: {selector}")
                        break
                if message_box:
                    break
            except Exception as e:
                print(f"[DEBUG] Selector {selector} failed: {str(e)}")
                continue
        
        if not message_box:
            print("[ERROR] Could not find message box")
            try:
                driver.save_screenshot('debug_no_messagebox.png')
                print("[DEBUG] Screenshot saved: debug_no_messagebox.png")
                with open('debug_page_source.html', 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                print("[DEBUG] Page source saved: debug_page_source.html")
            except:
                pass
            return False
        
        print(f"[DEBUG] Typing message: {message[:50]}...")
        message_box.click()
        time.sleep(0.5)
        
        try:
            message_box.clear()
        except:
            pass
        
        try:
            driver.execute_script("""
                var element = arguments[0];
                var text = arguments[1];
                element.focus();
                
                if (element.value !== undefined) {
                    element.value = text;
                    element.dispatchEvent(new Event('input', { bubbles: true }));
                    element.dispatchEvent(new Event('change', { bubbles: true }));
                } else {
                    element.textContent = text;
                    element.innerText = text;
                    element.dispatchEvent(new Event('input', { bubbles: true }));
                }
            """, message_box, message)
            print("[DEBUG] Message inserted via JavaScript")
        except:
            print("[DEBUG] JavaScript insert failed, using send_keys")
            message_filtered = message.encode('ascii', 'ignore').decode('ascii')
            message_box.send_keys(message_filtered)
        
        time.sleep(1)
        
        print("[DEBUG] Looking for send button...")
        send_button_selectors = [
            "button[name='Send']",
            "input[name='Send']",
            "button[value='Send']",
            "button[type='submit']",
            "input[type='submit']"
        ]
        
        send_button = None
        for selector in send_button_selectors:
            try:
                buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                for btn in buttons:
                    if btn.is_displayed():
                        send_button = btn
                        print(f"[DEBUG] Found send button with selector: {selector}")
                        break
                if send_button:
                    break
            except:
                continue
        
        if send_button:
            print("[DEBUG] Clicking send button...")
            send_button.click()
        else:
            print("[DEBUG] Sending with Enter key...")
            message_box.send_keys(Keys.RETURN)
        
        time.sleep(2)
        print("[+] Message sent successfully")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to send message: {str(e)}")
        import traceback
        traceback.print_exc()
        try:
            driver.save_screenshot('debug_error.png')
            print("[DEBUG] Error screenshot saved: debug_error.png")
        except:
            pass
        return False

def send_messages():
    print("[+] Starting Selenium-based message sender...")
    
    try:
        with open('convo.txt', 'r') as file:
            convo_id = file.read().strip()
            print(f"[DEBUG] Conversation ID: {convo_id}")
    except Exception as e:
        print(f"[ERROR] Reading convo.txt: {str(e)}")
        return
    
    try:
        with open('file.txt', 'r') as file:
            text_file_path = file.read().strip()
        with open(text_file_path, 'r') as file:
            messages = [line.strip() for line in file.readlines() if line.strip()]
            print(f"[DEBUG] Loaded {len(messages)} messages")
    except Exception as e:
        print(f"[ERROR] Reading messages: {str(e)}")
        return
    
    try:
        with open('hatersname.txt', 'r') as file:
            haters_name = file.read().strip()
    except:
        haters_name = ""
    
    try:
        with open('time.txt', 'r') as file:
            speed = int(file.read().strip())
    except:
        speed = 5
    
    driver = setup_driver()
    
    if not load_cookies_to_browser(driver):
        print("[ERROR] Failed to load cookies - stopping")
        driver.quit()
        return
    
    print("[+] Starting message loop...")
    try:
        while True:
            try:
                for i, message in enumerate(messages):
                    full_message = f"{haters_name} {message}" if haters_name else message
                    current_time = time.strftime("%Y-%m-%d %I:%M:%S %p")
                    
                    if send_message_selenium(driver, convo_id, full_message):
                        print(f"[+] Message {i+1}/{len(messages)} sent | {current_time}")
                    else:
                        print(f"[-] Failed to send message {i+1} | {current_time}")
                    
                    time.sleep(speed + random.uniform(-1, 1))
                
                print("[+] Message cycle completed. Restarting...")
            except Exception as e:
                print(f"[!] Error in message loop: {str(e)}")
                time.sleep(30)
    
    except KeyboardInterrupt:
        print("\n[+] Stopping message sender...")
    finally:
        driver.quit()
        print("[+] Browser closed")

if __name__ == "__main__":
    server_thread = threading.Thread(target=execute_server, daemon=True)
    server_thread.start()
    
    time.sleep(2)
    send_messages()
