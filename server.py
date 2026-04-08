"""
SmartParcel — TCP Server (single-threaded)

"""

import socket
import json
from datetime import datetime

HOST = "localhost"
PORT = 9000


parcels = {}
counter = 0

VALID_STATUSES = ["registered", "picked_up", "in_transit", "delivered"]


def generate_id():
    global counter
    counter += 1
    return f"PKG-{counter:04d}"


def handle_register(data):
    required = ["sender", "receiver", "address", "email"]
    for field in required:
        if field not in data or not data[field]:
            return {"status": "error", "message": f"Missing field: {field}"}

    parcel_id = generate_id()
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
    if parcel_id in parcels:
        return {"status": "ok", "parcel": parcels[parcel_id]}
    return {"status": "error", "message": "Parcel not found"}


def handle_update_status(data):
    parcel_id = data.get("parcel_id", "")
    new_status = data.get("new_status", "")

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


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    log(f"TCP server listening on {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server_socket.accept()
            log(f"Connection from {addr[0]}:{addr[1]}")
            try:
                raw = conn.recv(4096).decode("utf-8")
                if not raw:
                    log(f"Client {addr[0]} disconnected (empty recv)")
                    conn.close()
                    continue

                try:
                    request = json.loads(raw)
                except json.JSONDecodeError:
                    response = {"status": "error", "message": "Invalid JSON"}
                    conn.sendall(json.dumps(response).encode("utf-8"))
                    conn.close()
                    continue

                response = handle_request(request)
                action = request.get("action", "?").upper()
                pid = response.get("parcel_id", response.get("parcel", {}).get("parcel_id", ""))
                log(f"{action} {pid} from {addr[0]}")

                conn.sendall(json.dumps(response).encode("utf-8"))
            except ConnectionResetError:
                log(f"Connection reset by {addr[0]}")
            except Exception as e:
                log(f"Error: {e}")
            finally:
                conn.close()
    except KeyboardInterrupt:
        log("Server shutting down.")
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()
