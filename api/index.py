import os
import sys
import json
import urllib3
import requests
from http.server import BaseHTTPRequestHandler
from concurrent.futures import ThreadPoolExecutor
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Dynamic Multi-Path Protobuf Importer
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)
sys.path.insert(0, os.path.join(CURRENT_DIR, '..'))
sys.path.insert(0, os.path.join(CURRENT_DIR, 'Pb2'))
sys.path.insert(0, os.path.join(CURRENT_DIR, '..', 'Pb2'))

try:
    import follow_pb2
except ImportError:
    follow_pb2 = None

STATIC_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
STATIC_IV  = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

SESSION = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100, max_retries=1)
SESSION.mount('https://', adapter)

def encrypt_proto(payload_bytes: bytes) -> bytes:
    cipher = AES.new(STATIC_KEY, AES.MODE_CBC, STATIC_IV)
    return cipher.encrypt(pad(payload_bytes, AES.block_size))

def send_follow_request(target_id, jwt_token):
    """
    spin.py এর মতো BD এবং IND উভয় সার্ভারে ফলো পাঠানোর ট্রাই করবে
    """
    urls = [
        "https://clientbp.ggpolarbear.com/Follow",        # BD Server
        "https://client.ind.freefiremobile.com/Follow"     # IND Server
    ]

    if follow_pb2 is None:
        return False, None, "follow_pb2 module missing on server"

    try:
        req = follow_pb2.CSFollowReq()
        req.target_id = int(target_id)
        encrypted_data = encrypt_proto(req.SerializeToString())
    except Exception as e:
        return False, None, f"Protobuf encryption error: {str(e)}"

    headers = {
        "User-Agent": "UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
        "Accept": "*/*",
        "Accept-Encoding": "deflate, gzip",
        "Authorization": f"Bearer {jwt_token}",
        "X-Ga": "v1 1",
        "Releaseversion": "OB54",
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Unity-Version": "2022.3.47f1",
        "Connection": "keep-alive"
    }

    for url in urls:
        try:
            res = SESSION.post(url, headers=headers, data=encrypted_data, verify=False, timeout=8)
            if res.status_code == 200:
                proto_res = follow_pb2.CSFollowRes()
                proto_res.ParseFromString(res.content)
                return True, proto_res, ""
            elif res.status_code == 401:
                return False, None, "Token Expired (401)"
        except Exception:
            continue

    return False, None, "HTTP Server Error or Timeout"

def process_single_follow(target_id: str, jwt_token: str, uid: str = ""):
    """
    spin.py এর হুবহু লজিক অনুযায়ী রেজাল্ট জাজ করবে
    """
    ok, proto_res, err_msg = send_follow_request(target_id, jwt_token)
    if not ok:
        res_type = "TOKEN_EXPIRED" if "401" in err_msg else "FAILED"
        return {
            "uid": uid,
            "status": "failed",
            "result_type": res_type,
            "message": f"Server Error: {err_msg}",
            "should_save": False
        }

    fail_txt = str(proto_res.fail_info).lower() if proto_res.fail_info else ""

    # Check 1: Already Followed (✅ Saved)
    if "already" in fail_txt or "followed" in fail_txt:
        return {
            "uid": uid,
            "status": "already_followed",
            "result_type": "ALREADY_FOLLOWED",
            "message": "Already Followed (অলরেডি দেওয়া হয়ে গেছে)",
            "should_save": True
        }

    # Check 2: Fail Info from server (❌ NOT Saved - কোনো এরর থাকলে কখনোই সাকসেস হবে না)
    if proto_res.fail_info:
        return {
            "uid": uid,
            "status": "failed",
            "result_type": "FAILED",
            "message": f"Failed: {proto_res.fail_info}",
            "should_save": False
        }

    # Check 3: MUST HAVE PLAYED 3 MAP MATCHES! (❌ NOT Saved)
    if proto_res.remaining_play_count > 0:
        return {
            "uid": uid,
            "status": "need_matches",
            "result_type": "NEED_MATCHES",
            "remaining": proto_res.remaining_play_count,
            "message": f"Need 3 Maps Play ({proto_res.remaining_play_count} match remaining)",
            "should_save": False
        }

    # Check 4: Capacity Check (❌ NOT Saved)
    if hasattr(proto_res, 'remaining_follow_capacity') and proto_res.remaining_follow_capacity == 0:
        return {
            "uid": uid,
            "status": "no_capacity",
            "result_type": "NO_CAPACITY",
            "message": "Daily Capacity Reached (ক্যাপাসিটি শেষ)",
            "should_save": False
        }

    # TRULY SUCCESSFUL FOLLOW (✅ Saved)
    return {
        "uid": uid,
        "status": "success",
        "result_type": "SUCCESS",
        "message": "Follow Sent Successfully (সত্যি সত্যি ফলো গেছে)",
        "should_save": True
    }

class handler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, payload):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        self._send_json(200, {"status": "online", "service": "Garena Accurate Follow Engine v8.0"})

    def do_POST(self):
        try:
            content_len = int(self.headers.get('Content-Length', 0))
            raw_body = self.rfile.read(content_len)
            data = json.loads(raw_body.decode('utf-8'))

            target_id = str(data.get('target_id', '')).strip()
            if not target_id:
                self._send_json(400, {"status": "failed", "message": "Target UID is required."})
                return

            # Batch Follow Mode
            if "tokens" in data and isinstance(data["tokens"], list):
                tokens_list = data["tokens"]

                def worker(item):
                    if isinstance(item, dict):
                        tok = item.get("token", "")
                        acc_uid = item.get("uid", "")
                    else:
                        tok = str(item)
                        acc_uid = ""
                    return process_single_follow(target_id, tok, acc_uid)

                workers_count = min(60, max(10, len(tokens_list)))
                with ThreadPoolExecutor(max_workers=workers_count) as executor:
                    results = list(executor.map(worker, tokens_list))

                success_c       = sum(1 for r in results if r.get("result_type") == "SUCCESS")
                already_c       = sum(1 for r in results if r.get("result_type") == "ALREADY_FOLLOWED")
                need_map_c      = sum(1 for r in results if r.get("result_type") == "NEED_MATCHES")
                no_capacity_c   = sum(1 for r in results if r.get("result_type") == "NO_CAPACITY")
                token_expired_c = sum(1 for r in results if r.get("result_type") == "TOKEN_EXPIRED")
                other_failed_c  = sum(1 for r in results if r.get("result_type") == "FAILED")
                
                total_failed    = need_map_c + no_capacity_c + token_expired_c + other_failed_c
                total_saved     = success_c + already_c

                self._send_json(200, {
                    "status": "batch_completed",
                    "target_id": target_id,
                    "summary": {
                        "total_requested": len(tokens_list),
                        "total_saved": total_saved,
                        "success_count": success_c,
                        "already_count": already_c,
                        "total_failed": total_failed,
                        "breakdown": {
                            "need_map_count": need_map_c,
                            "no_capacity_count": no_capacity_c,
                            "token_expired_count": token_expired_c,
                            "other_failed_count": other_failed_c
                        }
                    },
                    "results": results
                })
                return

            # Single Follow Mode
            jwt_token = str(data.get('token', '')).strip()
            account_uid = str(data.get('uid', '')).strip()
            if not jwt_token:
                self._send_json(400, {"status": "failed", "message": "Token is required."})
                return

            result = process_single_follow(target_id, jwt_token, account_uid)
            self._send_json(200, result)

        except Exception as e:
            self._send_json(500, {"status": "error", "message": str(e)})
