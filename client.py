"""
SmartParcel — TCP Client

"""

import socket
import json

HOST = "localhost"
PORT = 9000


def send_request(request):
    """Connect to the server, send a JSON request, return the parsed response."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((HOST, PORT))
        sock.sendall(json.dumps(request).encode("utf-8"))
        raw = sock.recv(4096).decode("utf-8")
        sock.close()
        return json.loads(raw)
    except ConnectionRefusedError:
        print("ERROR: Could not connect to server. Is server.py running?")
        return None
    except socket.timeout:
        print("ERROR: Connection timed out.")
        return None


def main():
    print("=" * 55)
    print("SmartParcel TCP Client — Demo")
    print("=" * 55)


    print("\n--- Step 1: Register a parcel ---")
    req = {
        "action": "register",
        "data": {
            "sender": "Ali",
            "receiver": "Sara",
            "address": "Dubai Marina",
            "email": "sara@example.com",
        },
    }
    print(f"Sending: {json.dumps(req, indent=2)}")
    resp = send_request(req)
    if resp is None:
        return
    print(f"Response: {json.dumps(resp, indent=2)}")
    parcel_id = resp.get("parcel_id", "")


    print("\n--- Step 2: Lookup the parcel ---")
    req = {"action": "lookup", "data": {"parcel_id": parcel_id}}
    print(f"Sending: {json.dumps(req, indent=2)}")
    resp = send_request(req)
    print(f"Response: {json.dumps(resp, indent=2)}")


    print("\n--- Step 3: Update status to in_transit ---")
    req = {
        "action": "update_status",
        "data": {"parcel_id": parcel_id, "new_status": "in_transit"},
    }
    print(f"Sending: {json.dumps(req, indent=2)}")
    resp = send_request(req)
    print(f"Response: {json.dumps(resp, indent=2)}")


    print("\n--- Step 4: Verify status changed ---")
    req = {"action": "lookup", "data": {"parcel_id": parcel_id}}
    print(f"Sending: {json.dumps(req, indent=2)}")
    resp = send_request(req)
    print(f"Response: {json.dumps(resp, indent=2)}")

    
    print("\n--- Step 5: Test invalid action ---")
    req = {"action": "invalid_action", "data": {}}
    print(f"Sending: {json.dumps(req, indent=2)}")
    resp = send_request(req)
    print(f"Response: {json.dumps(resp, indent=2)}")

    
    print("\n--- Step 6: Test missing field ---")
    req = {"action": "register", "data": {"sender": "Ali"}}
    print(f"Sending: {json.dumps(req, indent=2)}")
    resp = send_request(req)
    print(f"Response: {json.dumps(resp, indent=2)}")

    print("\n" + "=" * 55)
    print("All tests complete.")
    print("=" * 55)


if __name__ == "__main__":
    main()
