#!/usr/bin/env python3
import threading
import queue
import socket
import sys
import termios
import tty
import atexit
import subprocess
import os
import signal

# Hardcoded proxy port (less common port)
PROXY_PORT = 9999

intercept = False
req_queue = queue.Queue()
original_term_settings = None

def setup_terminal():
    global original_term_settings
    if sys.stdin.isatty():
        original_term_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
        atexit.register(restore_terminal)

def restore_terminal():
    global original_term_settings
    if original_term_settings is not None:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, original_term_settings)

def print_banner():
    print(f"\n\033[1;97mnetzy-proxy-https\033[0m \033[2m— http/https intercepting proxy\033[0m")
    print(f"\033[38;5;111ms\033[0m toggle mode  \033[38;5;111mf\033[0m forward  \033[38;5;111md\033[0m drop\n")
    print(f"\033[2mProxy: 0.0.0.0:{PROXY_PORT}\033[0m")
    
    # Get local IP
    try:
        result = subprocess.run(['ip', 'route', 'get', '1'], capture_output=True, text=True)
        local_ip = result.stdout.split('src ')[1].split()[0] if 'src' in result.stdout else '<your-ip>'
    except:
        local_ip = '<your-ip>'
    
    print(f"\033[2mConfigure your device proxy to: \033[1m{local_ip}:{PROXY_PORT}\033[0m\n")

def parse_http_request(data):
    """Parse HTTP request and return method, host, path, headers"""
    try:
        lines = data.decode('utf-8', errors='ignore').split('\r\n')
        if not lines or not lines[0]:
            return None
        
        parts = lines[0].split(' ')
        if len(parts) < 3:
            return None
        
        method = parts[0]
        path = parts[1]
        
        headers = {}
        host = ""
        for line in lines[1:]:
            if not line:
                break
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()
                if key.strip().lower() == 'host':
                    host = value.strip()
        
        return {
            'method': method,
            'path': path,
            'host': host,
            'headers': headers,
            'raw': data
        }
    except:
        return None

def print_request(req_info, client_addr, is_https=False):
    """Pretty print HTTP/HTTPS request details"""
    if not req_info:
        return
    
    method = req_info['method']
    host = req_info['host']
    path = req_info['path']
    
    method_colors = {
        'GET': '\033[38;5;150m',
        'POST': '\033[38;5;217m',
        'PUT': '\033[38;5;222m',
        'DELETE': '\033[38;5;203m',
        'CONNECT': '\033[38;5;183m',
    }
    method_color = method_colors.get(method, '\033[38;5;183m')
    
    protocol = '\033[38;5;203mHTTPS\033[0m' if is_https else '\033[38;5;150mHTTP\033[0m'
    
    print(f"\033[38;5;111m{client_addr[0]}:{client_addr[1]}\033[0m  {protocol}  {method_color}{method}\033[0m  \033[38;5;222m{host}\033[0m\033[38;5;183m{path}\033[0m")
    
    important = ['user-agent', 'content-type', 'content-length', 'cookie', 'authorization']
    for h in important:
        if h in req_info['headers']:
            value = req_info['headers'][h]
            if len(value) > 60:
                value = value[:60] + "..."
            print(f"  \033[2m{h}: {value}\033[0m")
    
    queue_size = req_queue.qsize()
    if queue_size > 0:
        print(f"  \033[38;5;203mqueue: {queue_size}\033[0m")

def forward_http_request(client_sock, req_info, request_data):
    """Forward HTTP request to target server"""
    try:
        host = req_info['host']
        port = 80
        
        if ':' in host:
            host, port_str = host.split(':')
            port = int(port_str)
        
        target_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target_sock.settimeout(10)
        target_sock.connect((host, port))
        target_sock.sendall(request_data)
        
        while True:
            chunk = target_sock.recv(4096)
            if not chunk:
                break
            client_sock.sendall(chunk)
        
        target_sock.close()
        client_sock.close()
    except Exception as e:
        client_sock.close()

def forward_connect_tunnel(client_sock, host, port):
    """Create HTTPS tunnel for CONNECT requests"""
    try:
        target_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target_sock.settimeout(10)
        target_sock.connect((host, port))
        
        client_sock.sendall(b'HTTP/1.1 200 Connection Established\r\n\r\n')
        
        def forward(src, dst):
            try:
                while True:
                    data = src.recv(4096)
                    if not data:
                        break
                    dst.sendall(data)
            except:
                pass
            finally:
                try:
                    src.close()
                except:
                    pass
                try:
                    dst.close()
                except:
                    pass
        
        t1 = threading.Thread(target=forward, args=(client_sock, target_sock), daemon=True)
        t2 = threading.Thread(target=forward, args=(target_sock, client_sock), daemon=True)
        t1.start()
        t2.start()
    except Exception as e:
        client_sock.close()

def handle_client(client_sock, client_addr):
    """Handle incoming client connection"""
    try:
        data = client_sock.recv(4096, socket.MSG_PEEK)
        if not data:
            client_sock.close()
            return
        
        first_line = data.decode('utf-8', errors='ignore').split('\r\n')[0]
        parts = first_line.split(' ')
        
        if len(parts) >= 3 and parts[0] == 'CONNECT':
            # HTTPS CONNECT request
            host_port = parts[1]
            if ':' in host_port:
                host, port = host_port.rsplit(':', 1)
                port = int(port)
            else:
                host = host_port
                port = 443
            
            # Consume CONNECT request
            client_sock.recv(4096)
            
            req_info = {
                'method': 'CONNECT',
                'host': f"{host}:{port}",
                'path': '',
                'headers': {}
            }
            
            if intercept:
                print_request(req_info, client_addr, is_https=True)
                req_queue.put(('https', client_sock, req_info, host, port))
            else:
                print_request(req_info, client_addr, is_https=True)
                forward_connect_tunnel(client_sock, host, port)
        else:
            # Regular HTTP request
            data = b""
            while True:
                chunk = client_sock.recv(4096)
                if not chunk:
                    break
                data += chunk
                if b'\r\n\r\n' in data:
                    break
            
            if not data:
                client_sock.close()
                return
            
            req_info = parse_http_request(data)
            if not req_info:
                client_sock.close()
                return
            
            if intercept:
                print_request(req_info, client_addr, is_https=False)
                req_queue.put(('http', client_sock, req_info, data))
            else:
                print_request(req_info, client_addr, is_https=False)
                forward_http_request(client_sock, req_info, data)
    except Exception as e:
        client_sock.close()

def keyboard_handler():
    """Handle keyboard input for forward/drop"""
    global intercept
    while True:
        key = sys.stdin.read(1)
        
        if key == "s":
            intercept = not intercept
            if intercept:
                print(f"\n\033[38;5;203m[manual mode]\033[0m requests queued, press f/d to forward/drop\n")
            else:
                count = 0
                while not req_queue.empty():
                    item = req_queue.get()
                    if item[0] == 'https':
                        _, client_sock, req_info, host, port = item
                        forward_connect_tunnel(client_sock, host, port)
                    else:
                        _, client_sock, req_info, data = item
                        forward_http_request(client_sock, req_info, data)
                    count += 1
                if count > 0:
                    print(f"\n\033[38;5;150m[auto mode]\033[0m forwarded {count} queued requests\n")
                else:
                    print(f"\n\033[38;5;150m[auto mode]\033[0m auto-forwarding\n")
        
        elif key == "f":
            if intercept and not req_queue.empty():
                item = req_queue.get()
                remaining = req_queue.qsize()
                print(f"\033[38;5;150m→ forwarded\033[0m ({remaining} remaining)")
                
                if item[0] == 'https':
                    _, client_sock, req_info, host, port = item
                    forward_connect_tunnel(client_sock, host, port)
                else:
                    _, client_sock, req_info, data = item
                    forward_http_request(client_sock, req_info, data)
            elif intercept:
                print(f"\033[2m[queue empty]\033[0m")
        
        elif key == "d":
            if intercept and not req_queue.empty():
                item = req_queue.get()
                remaining = req_queue.qsize()
                print(f"\033[38;5;203m✗ dropped\033[0m ({remaining} remaining)")
                
                # Close socket to drop connection
                if item[0] == 'https':
                    item[1].close()
                else:
                    item[1].close()
            elif intercept:
                print(f"\033[2m[queue empty]\033[0m")

def kill_existing_process():
    """Kill any existing process using our port"""
    try:
        result = subprocess.run(
            ['lsof', '-ti', f':{PROXY_PORT}'],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    os.kill(int(pid), signal.SIGKILL)
                    print(f"\033[38;5;222m⚠\033[0m killed existing process on port {PROXY_PORT} (pid: {pid})")
                except:
                    pass
    except:
        pass

def main():
    # Kill any existing instance
    kill_existing_process()
    
    setup_terminal()
    print_banner()
    print(f"\033[38;5;150m[auto mode]\033[0m auto-forwarding (press s for manual)\n")
    
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_sock.bind(('0.0.0.0', PROXY_PORT))
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"\033[38;5;203m✗\033[0m Port {PROXY_PORT} already in use")
            print(f"\033[2mTrying to kill existing process...\033[0m")
            kill_existing_process()
            try:
                server_sock.bind(('0.0.0.0', PROXY_PORT))
                print(f"\033[38;5;150m✓\033[0m Port {PROXY_PORT} now available\n")
            except:
                print(f"\033[38;5;203m✗\033[0m Failed to bind to port {PROXY_PORT}")
                print(f"\033[2mTry: sudo lsof -ti :{PROXY_PORT} | xargs kill -9\033[0m")
                sys.exit(1)
        else:
            print(f"\033[38;5;203m✗\033[0m Failed to bind: {e}")
            sys.exit(1)
    
    server_sock.listen(50)
    
    kb_thread = threading.Thread(target=keyboard_handler, daemon=True)
    kb_thread.start()
    
    try:
        while True:
            client_sock, client_addr = server_sock.accept()
            threading.Thread(
                target=handle_client,
                args=(client_sock, client_addr),
                daemon=True
            ).start()
    except KeyboardInterrupt:
        print(f"\n\033[2m[shutdown]\033[0m")
        server_sock.close()
        restore_terminal()

if __name__ == "__main__":
    main()

