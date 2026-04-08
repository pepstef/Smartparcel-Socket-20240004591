"""
SmartParcel — Concurrent Load Test (5 clients)
NET 214 Network Programming — Spring 2026 — REFERENCE SOLUTION
"""

import socket
import json
import time
from concurrent.futures import ThreadPoolExecutor

HOST = "localhost"
PORT = 9000


def register_parcel(client_id):
    """Send a register request and return the result."""
    start = time.time()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((HOST, PORT))

        request = {
            "action": "register",
            "data": {
                "sender": f"Driver-{client_id}",
                "receiver": f"Customer-{client_id}",
                "address": f"Address-{client_id}",
                "email": f"customer{client_id}@example.com",
            },
        }
        sock.sendall(json.dumps(request).encode("utf-8"))
        raw = sock.recv(4096).decode("utf-8")
        sock.close()

        elapsed = round(time.time() - start, 3)
        response = json.loads(raw)
        return {
            "client_id": client_id,
            "success": response.get("status") == "ok",
            "parcel_id": response.get("parcel_id", ""),
            "time": elapsed,
        }
    except Exception as e:
        elapsed = round(time.time() - start, 3)
        return {
            "client_id": client_id,
            "success": False,
            "parcel_id": "",
            "time": elapsed,
            "error": str(e),
        }


def main():
    num_clients = 5
    print("=" * 60)
    print(f"SmartParcel Load Test — {num_clients} concurrent clients")
    print("=" * 60)

    overall_start = time.time()

    with ThreadPoolExecutor(max_workers=num_clients) as pool:
        results = list(pool.map(register_parcel, range(1, num_clients + 1)))

    overall_time = round(time.time() - overall_start, 3)

    print(f"\n{'Client':<10} {'Success':<10} {'Parcel ID':<15} {'Time (s)':<10}")
    print("-" * 45)
    for r in results:
        print(f"{r['client_id']:<10} {str(r['success']):<10} {r['parcel_id']:<15} {r['time']:<10}")

    successes = sum(1 for r in results if r["success"])
    avg_time = round(sum(r["time"] for r in results) / len(results), 3)

    print("-" * 45)
    print(f"Results: {successes}/{num_clients} succeeded")
    print(f"Total wall-clock time: {overall_time}s")
    print(f"Average response time: {avg_time}s")

    if successes == num_clients:
        print("\nPASS — All concurrent registrations succeeded!")
    else:
        print(f"\nFAIL — {num_clients - successes} requests failed.")


if __name__ == "__main__":
    main()
