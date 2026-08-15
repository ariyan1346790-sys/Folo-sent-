import os
import sys
import json
import urllib3
import requests
import traceback
import importlib.util
from http.server import BaseHTTPRequestHandler
from concurrent.futures import ThreadPoolExecutor
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==============================================================================
#      🔍 ALL-CASE INSENSITIVE SMART LOADER (নাম যেভাবেই থাক লোড করবে)
# ==============================================================================
follow_pb2 = None
LOAD_ERROR = None
ALL_FOUND_FILES = []

def smart_load_follow_pb2():
    global follow_pb2, LOAD_ERROR, ALL_FOUND_FILES
    
    # ১. সাধারণ নাম ট্রাই
    possible_module_names = ["follow_pb2", "Follow_pb2", "follow_Pb2", "FOLLOW_PB2"]
    for mod_name in possible_module_names:
        try:
            follow_pb2 = __import__(mod_name)
            return
        except Exception:
            pass

    # ২. লিনাক্স সার্ভারের সমস্ত ফোল্ডার স্ক্যান (Case-Insensitive)
    scan_roots = [
        os.path.dirname(os.path.abspath(__file__)),
        os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')),
        os.getcwd(),
        "/var/task"
    ]

    for root_dir in scan_roots:
        if not os.path.exists(root_dir):
            continue
        for r, d, f_list in os.walk(root_dir):
            for file in f_list:
                full_path = os.path.join(r, file)
                ALL_FOUND_FILES.append(full_path)
                
                # যদি ফাইলের নামের ভেতর 'follow' এবং 'pb2' থাকে (যেকোনো ছোট/বড় হাতের অক্ষরে)
                f_lower = file.lower()
                if "follow" in f_lower and "pb2" in f_lower and f_lower.endswith(".py"):
                    try:
                        spec = importlib.util.spec_from_file_location("follow_pb2", full_path)
                        mod = importlib.util.module_from_spec(spec)
                        sys.modules["follow_pb2"] = mod
                        spec.loader.exec_module(mod)
                        if hasattr(mod, 'CSFollowReq') and hasattr(mod, 'CSFollowRes'):
                            follow_pb2 = mod
                            return
                    except Exception as e:
                        LOAD_ERROR = f"Path {full_path} load error: {traceback.format_exc()}"

smart_load_follow_pb2()

# ==============================================================================
#                       OFFICIAL GARENA CRYPTO & KEYS
# ==============================================================================
STATIC_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
STATIC_IV  = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

SESSION = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100, max_retries=1)
SESSION.mount('https://', adapter)

def encrypt_proto(payload_bytes: bytes) -> bytes:
    cipher = AES.new(STATIC_KEY, AES.MODE_CBC, STATIC_IV)
    return cipher.encrypt(pad(payload_bytes, AES.block_size))

def send_follow_request(target_id, jwt_token):
    global follow_pb2
    if follow_pb2 is None:
        smart_load_follow_pb2()

    if follow_pb2 is None:
        return False, None, f"follow_pb2 missing. Found files: {ALL_FOUND_FILES[:10]}"

    urls = [
        "https://clientbp.ggpolarbear.com/Follow",
        "https://client.ind.freefiremobile.com/Follow"
    ]

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

    # 1. Already Followed
    if "already" in fail_txt or "followed" in fail_txt:
        return {
            "uid": uid,
            "status": "already_followed",
            "result_type": "ALREADY_FOLLOWED",
            "message": "Already Followed (অলরেডি দেওয়া হয়ে গেছে)",
            "should_save": True
        }

    # 2. Server Fail Info (Limit / Error)
    if proto_res.fail_info:
        return {
            "uid": uid,
            "status": "failed",
            "result_type": "FAILED",
            "message": f"Failed: {proto_res.fail_info}",
            "should_save": False
        }

    # 3. 3 Maps Play Needed
    if proto_res.remaining_play_count > 0:
        return {
            "uid": uid,
            "status": "need_matches",
            "result_type": "NEED_MATCHES",
            "remaining": proto_res.remaining_play_count,
            "message": f"Need 3 Maps Play ({proto_res.remaining_play_count} match remaining)",
            "should_save": False
        }

    # 4. Capacity Full
    if hasattr(proto_res, 'remaining_follow_capacity') and proto_res.remaining_follow_capacity == 0:
        return {
            "uid": uid,
            "status": "no_capacity",
            "result_type": "NO_CAPACITY",
            "message": "Daily Capacity Reached (ক্যাপাসিটি শেষ)",
            "should_save": False
        }

    # 5. Success
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

    # 🔍 ব্রাউজারে ডোমেইন ওপেন করলেই ডেব্যাগের পুরো রিপোর্ট দেখাবে
    def do_GET(self):
        self._send_json(200, {
            "status": "online",
            "proto_loaded": follow_pb2 is not None,
            "load_error": LOAD_ERROR,
            "server_files_detected": [f for f in ALL_FOUND_FILES if f.endswith(".py")]
        })

    def do_POST(self):
        try:
            content_len = int(self.headers.get('Content-Length', 0))
            raw_body = self.rfile.read(content_len)
            data = json.loads(raw_body.decode('utf-8'))

            target_id = str(data.get('target_id', '')).strip()
            if not target_id:
                self._send_json(400, {"status": "failed", "message": "Target UID is required."})
                return

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

            jwt_token = str(data.get('token', '')).strip()
            account_uid = str(data.get('uid', '')).strip()
            if not jwt_token:
                self._send_json(400, {"status": "failed", "message": "Token is required."})
                return

            result = process_single_follow(target_id, jwt_token, account_uid)
            self._send_json(200, result)

        except Exception as e:
            self._send_json(500, {"status": "error", "message": str(e)})
