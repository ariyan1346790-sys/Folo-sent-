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
except Exception:
    try:
        from . import follow_pb2
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
    """Built-in pure python varint encoder (Zero-dependency fallback)"""
    buf = bytearray()
    while n > 127:
        buf.append((n & 0x7F) | 0x80)
        n >>= 7
    buf.append(n & 0x7F)
    return bytes(buf)

def build_follow_payload(target_id: int) -> bytes:
    """Build CSFollowReq payload with protobuf or pure fallback"""
    if follow_pb2 is not None:
        try:
            req = follow_pb2.CSFollowReq()
            req.target_id = int(target_id)
            return encrypt_proto(req.SerializeToString())
        except Exception:
            pass
    
    # Pure-Python Raw Protobuf Payload for CSFollowReq (Field 1 = target_id)
    raw_proto = b'\x08' + encode_varint(int(target_id))
    return encrypt_proto(raw_proto)

def parse_follow_response(content: bytes):
    """Parse CSFollowRes using proto or raw byte scanner"""
    fail_info = ""
    remaining_play_count = 0
    remaining_follow_capacity = -1

    if follow_pb2 is not None:
        try:
            proto_res = follow_pb2.CSFollowRes()
            proto_res.ParseFromString(content)
            fail_info = str(proto_res.fail_info) if proto_res.fail_info else ""
            remaining_play_count = getattr(proto_res, 'remaining_play_count', 0)
            if hasattr(proto_res, 'remaining_follow_capacity'):
                remaining_follow_capacity = proto_res.remaining_follow_capacity
            return fail_info, remaining_play_count, remaining_follow_capacity
        except Exception:
            pass

    # Fallback byte scanner for fail_info / already followed
    try:
        txt = content.decode('utf-8', errors='ignore').lower()
        if "already" in txt or "followed" in txt:
            fail_info = "already followed"
    except Exception:
        pass

    return fail_info, remaining_play_count, remaining_follow_capacity

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
                fail_info, remaining_play_count, remaining_follow_capacity = parse_follow_response(res.content)
                fail_txt = fail_info.lower()

                # 1. Already Followed
                if "already" in fail_txt or "followed" in fail_txt:
                    return {
                        "uid": account_uid,
                        "status": "already_followed",
                        "result_type": "ALREADY_FOLLOWED",
                        "message": "Already Followed (অলরেডি দেওয়া ছিল)",
                        "should_save": True
                    }

                # 2. 3 Maps Play Needed
                if remaining_play_count > 0:
                    return {
                        "uid": account_uid,
                        "status": "need_matches",
                        "result_type": "NEED_MATCHES",
                        "remaining": remaining_play_count,
                        "message": f"Need 3 Maps Play ({remaining_play_count} left)",
                        "should_save": False
                    }

                # 3. Capacity Reached
                if remaining_follow_capacity == 0:
                    return {
                        "uid": account_uid,
                        "status": "no_capacity",
                        "result_type": "NO_CAPACITY",
                        "message": "Daily Capacity Reached",
                        "should_save": False
                    }

                # 4. Other Failures
                if fail_info:
                    return {
                        "uid": account_uid,
                        "status": "failed",
                        "result_type": "FAILED",
                        "message": f"Failed: {fail_info}",
                        "should_save": False
                    }

                # 5. Success
                return {
                    "uid": account_uid,
                    "status": "success",
                    "result_type": "SUCCESS",
                    "message": "Follow Sent Successfully",
                    "should_save": True
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
        self._send_json(200, {"status": "online", "engine": "Turbo Follow Dispatcher v6.0 (Zero-Fail Engine)"})

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
