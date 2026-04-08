
import socket
import json
import threading
import time
from datetime import datetime

HOST = "localhost"
TCP_PORT = 9000
UDP_PORT = 9001

# In-memory parcel store (shared across threads)
parcels = {}
counter = 0
lock = threading.Lock()
start_time = time.time()

VALID_STATUSES = ["registered", "picked_up", "in_transit", "delivered"]


def generate_id():
    global counter
    with lock:
        counter += 1
        return f"PKG-{counter:04d}"


def handle_register(data):
    required = ["sender", "receiver", "address", "email"]
    for field in required:
        if field not in data or not data[field]:
            return {"status": "error", "message": f"Missing field: {field}"}

    parcel_id = generate_id()
    with lock:
        parcels[parcel_id] = {
            "parcel_id": parcel_id,
            "sender": data["sender"],
            "receiver": data["receiver"],
            "address": data["address"],
            "email": data["email"],
            "status": "registered",
        }
    return {"status": "ok", "parcel_id": parcel_id}


def handle_lookup(data):
    parcel_id = data.get("parcel_id", "")
    with lock:
        if parcel_id in parcels:
            return {"status": "ok", "parcel": parcels[parcel_id]}
    return {"status": "error", "message": "Parcel not found"}


def handle_update_status(data):
    parcel_id = data.get("parcel_id", "")
    new_status = data.get("new_status", "")

    with lock:
        if parcel_id not in parcels:
            return {"status": "error", "message": "Parcel not found"}
        if new_status not in VALID_STATUSES:
            return {"status": "error", "message": "Invalid status"}
        parcels[parcel_id]["status"] = new_status
    return {"status": "ok", "parcel_id": parcel_id, "new_status": new_status}


def handle_request(request):
    action = request.get("action", "")
    data = request.get("data", {})

    if action == "register":
        return handle_register(data)
    elif action == "lookup":
        return handle_lookup(data)
    elif action == "update_status":
        return handle_update_status(data)
    else:
        return {"status": "error", "message": f"Unknown action: {action}"}


def log(message):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {message}")


def handle_client(conn, addr):
    """Handle a single TCP client in its own thread."""
    try:
        raw = conn.recv(4096).decode("utf-8")
        if not raw:
            log(f"Client {addr[0]} disconnected (empty recv)")
            return

        try:
            request = json.loads(raw)
        except json.JSONDecodeError:
            response = {"status": "error", "message": "Invalid JSON"}
            conn.sendall(json.dumps(response).encode("utf-8"))
            return

        response = handle_request(request)
        action = request.get("action", "?").upper()
        pid = response.get("parcel_id", response.get("parcel", {}).get("parcel_id", ""))
        log(f"{action} {pid} from {addr[0]} [thread={threading.current_thread().name}]")

        conn.sendall(json.dumps(response).encode("utf-8"))
    except ConnectionResetError:
        log(f"Connection reset by {addr[0]}")
    except Exception as e:
        log(f"Error handling {addr[0]}: {e}")
    finally:
        conn.close()


def udp_listener():
    """UDP health-check listener on port 9001."""
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind((HOST, UDP_PORT))
    log(f"UDP health-check listening on {HOST}:{UDP_PORT}")

    while True:
        data, addr = udp_sock.recvfrom(1024)
        uptime = round(time.time() - start_time, 1)
        response = json.dumps({"status": "healthy", "uptime_seconds": uptime})
        udp_sock.sendto(response.encode("utf-8"), addr)
        log(f"UDP PING from {addr[0]}:{addr[1]} — uptime={uptime}s")


def main():
    # Start UDP listener in a daemon thread
    udp_thread = threading.Thread(target=udp_listener, daemon=True)
    udp_thread.start()

    # Start TCP server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, TCP_PORT))
    server_socket.listen(10)
    log(f"TCP server listening on {HOST}:{TCP_PORT} (multi-threaded)")

    try:
        while True:
            conn, addr = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
    except KeyboardInterrupt:
        log("Server shutting down.")
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()
