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
        'authority': 'www.facebook.com',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.facebook.com',
        'referer': f'https://www.facebook.com/messages/t/{convo_id}',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
    }
    
    session = requests.Session()
    for name, value in cookies.items():
        session.cookies.set(name, value)
    
    try:
        print(f"[DEBUG] Loading conversation page...")
        res = session.get(f'https://www.facebook.com/messages/t/{convo_id}', headers=headers)
        print(f"[DEBUG] Page response status: {res.status_code}")
        
        if res.status_code != 200:
            print(f"[ERROR] Failed to load page. Status: {res.status_code}")
            return False
        
        fb_dtsg = None
        jazoest = None
        
        token_patterns = [
            r'"token":"([^"]+)"',
            r'"DTSGInitialData"[^}]*"token":"([^"]+)"',
            r'name="fb_dtsg"[^>]*value="([^"]+)"',
            r'\["DTSGInitData"[^\]]*"([^"]+)"'
        ]
        
        for pattern in token_patterns:
            match = re.search(pattern, res.text)
            if match:
                fb_dtsg = match
                print(f"[DEBUG] fb_dtsg found using pattern: {pattern[:30]}...")
                break
        
        jazoest_patterns = [
            r'jazoest=(\d+)',
            r'"jazoest":"(\d+)"',
            r'&amp;jazoest=(\d+)'
        ]
        
        for pattern in jazoest_patterns:
            match = re.search(pattern, res.text)
            if match:
                jazoest = match
                print(f"[DEBUG] jazoest found: {match.group(1)}")
                break
        
        if not fb_dtsg or not jazoest:
            print("[ERROR] Could not extract required tokens from page")
            print("[DEBUG] Saving HTML response to debug.html for inspection...")
            with open('debug.html', 'w', encoding='utf-8') as f:
                f.write(res.text[:100000])
            print("[DEBUG] Check debug.html to inspect the page source")
            print("[HINT] Your cookies might be expired. Please update cookies.txt with fresh cookies")
            return False
            
        print(f"[DEBUG] Tokens extracted successfully")
        
        form_data = {
            'fb_dtsg': fb_dtsg.group(1),
            'jazoest': jazoest.group(1),
            'body': message,
            'send': 'Send',
            'tids': f'cid.{convo_id}',
            '__user': cookies['c_user']
        }
        
        print(f"[DEBUG] Sending message...")
        response = session.post('https://www.facebook.com/messages/send/', data=form_data, headers=headers)
        print(f"[DEBUG] Facebook response status: {response.status_code}")
        
        if response.ok:
            return True
        else:
            print(f"[DEBUG] Response content preview: {response.text[:500]}")
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
                
                time.sleep(speed + random.uniform(-1, 1))  # Randomize delay
            
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
