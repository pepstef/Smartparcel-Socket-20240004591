"""
SmartParcel — UDP Health Check Client
NET 214 Network Programming — Spring 2026 — REFERENCE SOLUTION
"""

import socket
import json

HOST = "localhost"
UDP_PORT = 9001


def main():
    print("SmartParcel UDP Health Check")
    print("-" * 35)

    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.settimeout(3)

    try:
        udp_sock.sendto(b"ping", (HOST, UDP_PORT))
        raw, addr = udp_sock.recvfrom(1024)
        response = json.loads(raw.decode("utf-8"))
        print(f"Server: {addr[0]}:{addr[1]}")
        print(f"Status: {response['status']}")
        print(f"Uptime: {response['uptime_seconds']} seconds")
    except socket.timeout:
        print("ERROR: No response from server (timeout).")
        print("Is threaded_server.py running?")
    except ConnectionRefusedError:
        print("ERROR: Connection refused. Is threaded_server.py running?")
    finally:
        udp_sock.close()


if __name__ == "__main__":
    main()
