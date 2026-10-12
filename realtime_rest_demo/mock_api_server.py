"""
LOCAL STAND-IN FOR THE PUBLIC APIs (optional, works without internet)

Serves the same URLs and JSON shapes as the two public APIs, with values that keep
changing. Use it if the venue Wi-Fi blocks the real APIs, or to practise offline.

    python3 mock_api_server.py            # leave it running in one Terminal tab
    python3 ingest_rest_api.py --base-url http://127.0.0.1:8099        # in another tab
    python3 ingest_rest_api.py --source iss --base-url http://127.0.0.1:8099
"""
import json
import math
import random
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

PRICES = {"BTC-USD": 65000.0, "ETH-USD": 3200.0}


class Handler(BaseHTTPRequestHandler):
    def _send(self, payload, code=200):
        data = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parts = self.path.strip("/").split("/")
        # /v2/prices/BTC-USD/spot   (same shape as the Coinbase API)
        if len(parts) == 4 and parts[:2] == ["v2", "prices"] and parts[3] == "spot":
            sym = parts[2]
            if sym == "BAD-USD":                                   # used to test the validation
                return self._send({"data": {"base": "BAD", "currency": "USD", "amount": "-5.0"}})
            if sym not in PRICES:
                return self._send({"errors": [{"message": "not found"}]}, 404)
            PRICES[sym] *= 1 + random.uniform(-0.0006, 0.0006)
            base, cur = sym.split("-")
            return self._send({"data": {"base": base, "currency": cur, "amount": f"{PRICES[sym]:.2f}"}})
        # /v1/satellites/25544   (same shape as the wheretheiss.at API)
        if parts == ["v1", "satellites", "25544"]:
            t = time.time()
            return self._send({"name": "iss", "id": 25544, "latitude": 51.6 * math.sin(t / 900), "longitude": ((t / 12) % 360) - 180,
                               "altitude": 420 + 5 * math.sin(t / 300), "velocity": 27580 + 20 * math.sin(t / 200),
                               "visibility": "daylight", "timestamp": int(t), "units": "kilometers"})
        self._send({"error": "unknown path"}, 404)

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    print("Mock API on http://127.0.0.1:8099  (Ctrl+C to stop)")
    HTTPServer(("127.0.0.1", 8099), Handler).serve_forever()
