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

# Dynamic Multi-Path Importer for follow_pb2
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)
sys.path.insert(0, os.path.join(CURRENT_DIR, '..'))
sys.path.insert(0, os.path.join(CURRENT_DIR, '..', 'Pb2'))
sys.path.insert(0, os.path.join(CURRENT_DIR, 'Pb2'))

follow_pb2 = None
try:
    import follow_pb2
    from google.protobuf.json_format import MessageToDict
except Exception:
    try:
        from . import follow_pb2
        from google.protobuf.json_format import MessageToDict
    except Exception:
        follow_pb2 = None

STATIC_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
STATIC_IV  = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

# High-Capacity Reusable Session Connection Pool
SESSION = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100, max_retries=1)
SESSION.mount('https://', adapter)

def encrypt_proto(payload_bytes: bytes) -> bytes:
    cipher = AES.new(STATIC_KEY, AES.MODE_CBC, STATIC_IV)
    return cipher.encrypt(pad(payload_bytes, AES.block_size))

def encode_varint(n: int) -> bytes:
    buf = bytearray()
    while n > 127:
        buf.append((n & 0x7F) | 0x80)
        n >>= 7
    buf.append(n & 0x7F)
    return bytes(buf)

def build_follow_payload(target_id: int) -> bytes:
    if follow_pb2 is not None:
        try:
            req = follow_pb2.CSFollowReq()
            req.target_id = int(target_id)
            return encrypt_proto(req.SerializeToString())
        except Exception:
            pass
    raw_proto = b'\x08' + encode_varint(int(target_id))
    return encrypt_proto(raw_proto)

def analyze_follow_result(content: bytes):
    """
    নিখুঁতভাবে যাচাই করবে ফলো আসলেই গেছে নাকি ম্যাচ বাকি বা ফেইল্ড
    """
    if follow_pb2 is not None:
        try:
            proto_res = follow_pb2.CSFollowRes()
            proto_res.ParseFromString(content)
            fail_txt = str(proto_res.fail_info).lower() if proto_res.fail_info else ""

            # ১. অলরেডি ফলো দেওয়া থাকলে
            if "already" in fail_txt or "followed" in fail_txt:
                return "ALREADY_FOLLOWED", "Already Followed (অলরেডি ছিল)", True, 0

            # ২. ৩টি ম্যাচ খেলা না থাকলে
            if getattr(proto_res, 'remaining_play_count', 0) > 0:
                rem = proto_res.remaining_play_count
                return "NEED_MATCHES", f"Need 3 Maps Play ({rem} remaining)", False, rem

            # ৩. ফলো লিমিট শেষ হলে
            if hasattr(proto_res, 'remaining_follow_capacity') and proto_res.remaining_follow_capacity == 0:
                return "NO_CAPACITY", "Daily Follow Capacity Reached", False, 0

            # ৪. কোনো ফেইল ইনফো থাকলে
            if proto_res.fail_info:
                return "FAILED", f"Failed: {proto_res.fail_info}", False, 0

            # ৫. নিশ্চিত ট্রু সাকসেস
            return "SUCCESS", "Follow Sent Successfully", True, 0

        except Exception:
            pass

    # Fallback RAW scanner
    txt = content.decode('utf-8', errors='ignore').lower()
    if "already" in txt or "followed" in txt:
        return "ALREADY_FOLLOWED", "Already Followed (অলরেডি ছিল)", True, 0
    
    # যদি কন্টেন্ট ছোট বা খালি থাকে তবে এটি ফেইল্ড (ফেক সাকসেস বন্ধ করতে)
    if len(content) < 2:
        return "FAILED", "Invalid server response", False, 0

    return "SUCCESS", "Follow Sent Successfully", True, 0

def execute_single_follow(target_id: str, jwt_token: str, account_uid: str = ""):
    urls = [
        "https://clientbp.ggpolarbear.com/Follow",        # BD Server
        "https://client.ind.freefiremobile.com/Follow"     # IND Server
    ]

    try:
        encrypted_data = build_follow_payload(int(target_id))
    except Exception as e:
        return {
            "uid": account_uid,
            "status": "failed",
            "result_type": "FAILED",
            "message": f"Encryption error: {str(e)}",
            "should_save": False
        }

    headers = {
        "User-Agent": "UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
        "Accept": "*/*",
        "Accept-Encoding": "deflate, gzip",
        "Authorization": f"Bearer {jwt_token}",
        "X-Ga": "v1 1",
        "Releaseversion": "OB54",
        "Content-Type": "application/x-www-form-urlencoded",
        "Connection": "keep-alive"
    }

    for url in urls:
        try:
            res = SESSION.post(url, headers=headers, data=encrypted_data, verify=False, timeout=6)
            if res.status_code == 200:
                res_type, msg, should_save, rem_maps = analyze_follow_result(res.content)
                return {
                    "uid": account_uid,
                    "status": res_type.lower(),
                    "result_type": res_type,
                    "remaining": rem_maps,
                    "message": msg,
                    "should_save": should_save
                }
            elif res.status_code == 401:
                return {
                    "uid": account_uid,
                    "status": "token_expired",
                    "result_type": "TOKEN_EXPIRED",
                    "message": "Token Expired (401)",
                    "should_save": False
                }
        except Exception:
            continue

    return {
        "uid": account_uid,
        "status": "failed",
        "result_type": "FAILED",
        "message": "Network/Server Timeout",
        "should_save": False
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
        self._send_json(200, {"status": "online", "service": "Garena Turbo Follow Engine v7.0 (Strict Accurate Mode)"})

    def do_POST(self):
        try:
            content_len = int(self.headers.get('Content-Length', 0))
            raw_body = self.rfile.read(content_len)
            data = json.loads(raw_body.decode('utf-8'))

            target_id = str(data.get('target_id', '')).strip()
            if not target_id:
                self._send_json(400, {"status": "failed", "message": "Target UID required."})
                return

            # Batch Execution Mode
            if "tokens" in data and isinstance(data["tokens"], list):
                tokens_list = data["tokens"]
                
                def worker(item):
                    if isinstance(item, dict):
                        tok = item.get("token", "")
                        acc_uid = item.get("uid", "")
                    else:
                        tok = str(item)
                        acc_uid = ""
                    return execute_single_follow(target_id, tok, acc_uid)

                workers_count = min(70, max(10, len(tokens_list)))
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

            # Single Execution Mode
            jwt_token = str(data.get('token', '')).strip()
            account_uid = str(data.get('uid', '')).strip()

            if not jwt_token:
                self._send_json(400, {"status": "failed", "message": "Token is required."})
                return

            result = execute_single_follow(target_id, jwt_token, account_uid)
            self._send_json(200, result)

        except Exception as e:
            self._send_json(500, {"status": "error", "message": str(e)})
