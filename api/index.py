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

# ==============================================================================
#                 🛠️ EMBEDDED FOLLOW PROTOBUF COMPILER ENGINE
# ==============================================================================
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder

try:
    from google.protobuf import runtime_version as _runtime_version
    _runtime_version.ValidateProtobufRuntimeVersion(
        _runtime_version.Domain.PUBLIC, 7, 35, 1, '', 'follow.proto'
    )
except Exception:
    pass

_sym_db = _symbol_database.Default()

DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0c\x66ollow.proto\x12\x05proto\" \n\x0b\x43SFollowReq\x12\x11\n\ttarget_id\x18\x01 \x01(\x04\"\xbc\x01\n\x0b\x43SFollowRes\x12%\n\x04info\x18\x01 \x01(\x0b\x32\x17.proto.AccountInfoBasic\x12\x1c\n\x14remaining_play_count\x18\x02 \x01(\r\x12!\n\x19remaining_follow_capacity\x18\x03 \x01(\r\x12\x32\n\rcreator_stats\x18\x04 \x01(\x0b\x32\x1b.proto.WorkshopCreatorStats\x12\x11\n\tfail_info\x18\x05 \x01(\t\"\xe2\x01\n\x0e\x41\x63\x63ountPrefers\x12\x15\n\rhide_my_lobby\x18\x01 \x01(\x08\x12\x1c\n\x14pregame_show_choices\x18\x02 \x03(\r\x12\x1f\n\x17\x62r_pregame_show_choices\x18\x03 \x03(\r\x12\x1a\n\x12hide_personal_info\x18\x04 \x01(\x08\x12\x1f\n\x17\x64isable_friend_spectate\x18\x05 \x01(\x08\x12\x17\n\x0fhide_occupation\x18\x06 \x01(\x08\x12$\n\x1c\x63s_peak_pregame_show_choices\x18\x07 \x03(\r\"\x84\x01\n\x10\x45xternalIconInfo\x12\x15\n\rexternal_icon\x18\x01 \x01(\t\x12)\n\x06status\x18\x02 \x01(\x0e\x32\x19.proto.ExternalIconStatus\x12.\n\tshow_type\x18\x03 \x01(\x0e\x32\x1b.proto.ExternalIconShowType\"\xcc\x01\n\x14LeaderboardTitleInfo\x12\x1f\n\x17weapon_power_title_info\x18\x01 \x03(\r\x12\x1c\n\x14guild_war_title_info\x18\x02 \x03(\r\x12\x1a\n\x12ranking_title_info\x18\x03 \x03(\r\x12\x1b\n\x13title_first_receive\x18\x04 \x01(\x08\x12\x1a\n\x12\x63s_peak_title_info\x18\x05 \x03(\r\x12 \n\x18peak_title_first_receive\x18\x06 \x01(\x08\"\xbb\x03\n\x0fSocialBasicInfo\x12\x12\n\naccount_id\x18\x01 \x01(\x04\x12\x1d\n\x06gender\x18\x02 \x01(\x0e\x32\r.proto.Gender\x12\x10\n\x08language\x18\x03 \x01(\r\x12&\n\x0btime_online\x18\x04 \x01(\x0e\x32\x11.proto.TimeOnline\x12&\n\x0btime_active\x18\x05 \x01(\x0e\x32\x11.proto.TimeActive\x12\x12\n\nbattle_tag\x18\x06 \x03(\r\x12\x12\n\nsocial_tag\x18\x07 \x03(\r\x12&\n\x0bmode_prefer\x18\x08 \x01(\x0e\x32\x11.proto.ModePrefer\x12\x11\n\tsignature\x18\t \x01(\t\x12\"\n\trank_show\x18\n \x01(\x0e\x32\x0f.proto.RankShow\x12\x18\n\x10\x62\x61ttle_tag_count\x18\x0b \x03(\r\x12!\n\x19signature_ban_expire_time\x18\x0c \x01(\x03\x12\x37\n\x12leaderboard_titles\x18\r \x01(\x0b\x32\x1b.proto.LeaderboardTitleInfo\x12\x16\n\x0ephoto_wall_url\x18\x0e \x01(\t\"t\n#SocialHighLightsWithSocialBasicInfo\x12\x1a\n\x12social_high_lights\x18\x01 \x03(\r\x12\x31\n\x11social_basic_info\x18\x02 \x01(\x0b\x32\x16.proto.SocialBasicInfo\"C\n\tBadgeInfo\x12$\n\nbadge_type\x18\x01 \x01(\x0e\x32\x10.proto.BadgeType\x12\x10\n\x08sub_type\x18\x02 \x01(\r\"\xbc\x01\n\x14PrimePrivilegeDetail\x12\x12\n\naccount_id\x18\x01 \x01(\x04\x12\x13\n\x0bprime_level\x18\x02 \x01(\r\x12\x19\n\x11privilege_id_list\x18\x03 \x03(\r\x12\x16\n\x0emonthly_points\x18\x04 \x01(\x05\x12\x17\n\x0f\x61nnually_points\x18\x05 \x01(\x05\x12\x12\n\nsum_points\x18\x06 \x01(\x05\x12\x1b\n\x13sharee_remain_times\x18\x07 \x01(\r\"\xbe\x01\n\x0c\x42lacklistRes\x12\x12\n\naccount_id\x18\x01 \x01(\x04\x12\x11\n\tdevice_id\x18\x02 \x01(\t\x12\x12\n\nban_reason\x18\x03 \x01(\r\x12\x10\n\x08\x62\x61n_time\x18\x04 \x01(\r\x12\x19\n\x11\x62\x61n_reason_detail\x18\x05 \x01(\t\x12\x17\n\x0fis_in_blacklist\x18\x06 \x01(\x08\x12\x1b\n\x13\x62\x61n_expire_duration\x18\x07 \x01(\r\x12\x10\n\x08\x62\x61n_type\x18\x08 \x01(\t\"6\n\x18\x43reatorPrivilegeSwitches\x12\x1a\n\x12\x64isable_name_color\x18\x01 \x01(\x08\"\x91\x01\n\x1aWorkshopAccountSummaryInfo\x12\x12\n\naccount_id\x18\x01 \x01(\x04\x12\x0b\n\x03\x65xp\x18\x02 \x01(\r\x12\x15\n\rcreator_level\x18\x03 \x01(\r\x12;\n\x12privilege_switches\x18\x04 \x01(\x0b\x32\x1f.proto.CreatorPrivilegeSwitches\"\xa6\x02\n\tSparkInfo\x12 \n\x05state\x18\x01 \x01(\x0e\x32\x11.proto.SparkState\x12\r\n\x05level\x18\x02 \x01(\r\x12\x0b\n\x03\x65xp\x18\x03 \x01(\x04\x12\x19\n\x11login_streak_days\x18\x04 \x01(\r\x12\x0e\n\x06temper\x18\x05 \x01(\r\x12\x1b\n\x13\x61ppearance_item_ids\x18\x06 \x03(\r\x12 \n\x18\x64ormant_recover_progress\x18\x07 \x01(\r\x12%\n\x1d\x65xtinguished_recover_progress\x18\x08 \x01(\r\x12\x18\n\x10\x61ppearance_stage\x18\t \x01(\r\x12\x1e\n\x16stage_appearance_items\x18\n \x03(\r\x12\x10\n\x08\x63olor_id\x18\x0b \x01(\r\"S\n\x15\x41\x63\x63ountBasicSparkInfo\x12\x0f\n\x07\x63laimed\x18\x01 \x01(\x08\x12)\n\x0fuser_spark_info\x18\x02 \x01(\x0b\x32\x10.proto.SparkInfo\"\xa8\x12\n\x10\x41\x63\x63ountInfoBasic\x12\x12\n\naccount_id\x18\x01 \x01(\x04\x12\x14\n\x0c\x61\x63\x63ount_type\x18\x02 \x01(\r\x12\x10\n\x08nickname\x18\x03 \x01(\t\x12\x13\n\x0b\x65xternal_id\x18\x04 \x01(\t\x12\x0e\n\x06region\x18\x05 \x01(\t\x12\r\n\x05level\x18\x06 \x01(\r\x12\x0b\n\x03\x65xp\x18\x07 \x01(\r\x12\x15\n\rexternal_type\x18\x08 \x01(\r\x12\x15\n\rexternal_name\x18\t \x01(\t\x12\x15\n\rexternal_icon\x18\n \x01(\t\x12\x11\n\tbanner_id\x18\x0b \x01(\r\x12\x10\n\x08head_pic\x18\x0c \x01(\r\x12\x11\n\tclan_name\x18\r \x01(\t\x12\x0c\n\x04rank\x18\x0e \x01(\r\x12\x16\n\x0eranking_points\x18\x0f \x01(\r\x12\x0c\n\x04role\x18\x10 \x01(\r\x12\x16\n\x0ehas_elite_pass\x18\x11 \x01(\x08\x12\x11\n\tbadge_cnt\x18\x12 \x01(\r\x12\x10\n\x08\x62\x61\x64ge_id\x18\x13 \x01(\r\x12\x11\n\tseason_id\x18\x14 \x01(\r\x12\r\n\x05liked\x18\x15 \x01(\r\x12\x12\n\nis_deleted\x18\x16 \x01(\x08\x12\x11\n\tshow_rank\x18\x17 \x01(\x08\x12\x15\n\rlast_login_at\x18\x18 \x01(\x03\x12\x14\n\x0c\x65xternal_uid\x18\x19 \x01(\x04\x12\x11\n\treturn_at\x18\x1a \x01(\x03\x12\x1e\n\x16\x63hampionship_team_name\x18\x1b \x01(\t\x12$\n\x1c\x63hampionship_team_member_num\x18\x1c \x01(\r\x12\x1c\n\x14\x63hampionship_team_id\x18\x1d \x01(\x04\x12\x0f\n\x07\x63s_rank\x18\x1e \x01(\r\x12\x19\n\x11\x63s_ranking_points\x18\x1f \x01(\r\x12\x19\n\x11weapon_skin_shows\x18  \x03(\r\x12\x0e\n\x06pin_id\x18! \x01(\r\x12\x19\n\x11is_cs_ranking_ban\x18\" \x01(\x08\x12\x10\n\x08max_rank\x18# \x01(\r\x12\x13\n\x0b\x63s_max_rank\x18$ \x01(\r\x12\x1a\n\x12max_ranking_points\x18% \x01(\r\x12\x15\n\rgame_bag_show\x18& \x01(\r\x12\x15\n\rpeak_rank_pos\x18\' \x01(\r\x12\x18\n\x10\x63s_peak_rank_pos\x18( \x01(\r\x12.\n\x0f\x61\x63\x63ount_prefers\x18) \x01(\x0b\x32\x15.proto.AccountPrefers\x12\x1f\n\x17periodic_ranking_points\x18* \x01(\r\x12\x15\n\rperiodic_rank\x18+ \x01(\r\x12\x11\n\tcreate_at\x18, \x01(\x03\x12\x37\n\x16veteran_leave_days_tag\x18- \x01(\x0e\x32\x17.proto.VeteranLeaveDays\x12\x1b\n\x13selected_item_slots\x18. \x03(\r\x12\x35\n\x10pre_veteran_type\x18/ \x01(\x0e\x32\x1b.proto.PreVeteranActionType\x12\r\n\x05title\x18\x30 \x01(\r\x12\x33\n\x12\x65xternal_icon_info\x18\x31 \x01(\x0b\x32\x17.proto.ExternalIconInfo\x12\x17\n\x0frelease_version\x18\x32 \x01(\t\x12\x1b\n\x13veteran_expire_time\x18\x33 \x01(\x04\x12\x14\n\x0cshow_br_rank\x18\x34 \x01(\x08\x12\x14\n\x0cshow_cs_rank\x18\x35 \x01(\x08\x12\x0f\n\x07\x63lan_id\x18\x36 \x01(\x04\x12\x15\n\rclan_badge_id\x18\x37 \x01(\r\x12\x19\n\x11\x63ustom_clan_badge\x18\x38 \x01(\t\x12\x1d\n\x15use_custom_clan_badge\x18\x39 \x01(\x08\x12\x15\n\rclan_frame_id\x18: \x01(\r\x12\x18\n\x10membership_state\x18; \x01(\x08\x12\x1a\n\x12select_occupations\x18< \x03(\r\x12V\n\"social_high_lights_with_basic_info\x18= \x01(\x0b\x32*.proto.SocialHighLightsWithSocialBasicInfo\x12\x17\n\x0f\x61\x62_test_choices\x18> \x03(\r\x12\x15\n\ritem_tag_info\x18? \x03(\r\x12\x11\n\trank_sort\x18@ \x01(\r\x12\x14\n\x0c\x63s_rank_sort\x18\x41 \x01(\r\x12\x12\n\nhippo_rank\x18\x42 \x01(\r\x12\x1c\n\x14hippo_ranking_points\x18\x43 \x01(\r\x12\x16\n\x0ehippo_max_rank\x18\x44 \x01(\r\x12\x17\n\x0fshow_hippo_rank\x18\x45 \x01(\x08\x12\x1a\n\x12hippo_total_profit\x18\x46 \x01(\r\x12\x19\n\x11hippo_total_worth\x18G \x01(\r\x12\x18\n\x10mode_stats_infos\x18H \x03(\r\x12$\n\nbadge_info\x18I \x01(\x0b\x32\x10.proto.BadgeInfo\x12;\n\x16prime_privilege_detail\x18J \x01(\x0b\x32\x1b.proto.PrimePrivilegeDetail\x12\x16\n\x0e\x63s_peak_points\x18K \x01(\r\x12\x1d\n\x15\x64isplay_cs_peak_point\x18L \x01(\x08\x12#\n\x1b\x63s_peak_tournament_rank_pos\x18M \x01(\r\x12\x14\n\x0c\x61vatar_frame\x18N \x01(\r\x12&\n\tblacklist\x18O \x01(\x0b\x32\x13.proto.BlacklistRes\x12@\n\x15workshop_summary_info\x18P \x01(\x0b\x32!.proto.WorkshopAccountSummaryInfo\x12\x30\n\nspark_info\x18Q \x01(\x0b\x32\x1c.proto.AccountBasicSparkInfo\x12\x31\n\x11social_basic_info\x18R \x01(\x0b\x32\x16.proto.SocialBasicInfo\x12\x1f\n\x17photo_wall_ban_end_time\x18S \x01(\r\x12\x1a\n\x12show_emulator_flag\x18T \x01(\x08\x12\x1c\n\x14is_homepage_punished\x18U \x01(\x08\"\xca\x01\n\x14WorkshopCreatorStats\x12\x12\n\naccount_id\x18\x01 \x01(\x04\x12\x16\n\x0e\x66ollower_count\x18\x02 \x01(\r\x12\x0b\n\x03\x65xp\x18\x03 \x01(\r\x12\x13\n\x0blevel_infos\x18\x04 \x03(\r\x12\x15\n\rawarded_level\x18\x05 \x03(\r\x12\x0b\n\x03\x62io\x18\x06 \x01(\t\x12\x13\n\x0bpinned_maps\x18\x07 \x03(\r\x12\x18\n\x10latest_update_at\x18\x08 \x01(\x03\x12\x11\n\tmap_count\x18\t \x01(\r*P\n\x0c\x46ollowerType\x12\x15\n\x11\x46ollowerType_NONE\x10\x00\x12\x14\n\x10\x46ollowerType_YES\x10\x01\x12\x13\n\x0f\x46ollowerType_NO\x10\x02*\xa0\x01\n\x10VeteranLeaveDays\x12\x19\n\x15VeteranLeaveDays_NONE\x10\x00\x12\x1a\n\x16VeteranLeaveDays_SHORT\x10\x01\x12\x1b\n\x17VeteranLeaveDays_NORMAL\x10\x02\x12\x19\n\x15VeteranLeaveDays_LONG\x10\x03\x12\x1d\n\x19VeteranLeaveDays_VERYLONG\x10\x04*w\n\x14PreVeteranActionType\x12\x1d\n\x19PreVeteranActionType_NONE\x10\x00\x12!\n\x1dPreVeteranActionType_ACTIVITY\x10\x01\x12\x1d\n\x19PreVeteranActionType_BUFF\x10\x02*s\n\x12\x45xternalIconStatus\x12\x1b\n\x17\x45xternalIconStatus_NONE\x10\x00\x12!\n\x1d\x45xternalIconStatus_NOT_IN_USE\x10\x01\x12\x1d\n\x19\x45xternalIconStatus_IN_USE\x10\x02*t\n\x14\x45xternalIconShowType\x12\x1d\n\x19\x45xternalIconShowType_NONE\x10\x00\x12\x1f\n\x1b\x45xternalIconShowType_FRIEND\x10\x01\x12\x1c\n\x18\x45xternalIconShowType_ALL\x10\x02*T\n\x06Gender\x12\x0f\n\x0bGender_NONE\x10\x00\x12\x0f\n\x0bGender_MALE\x10\x01\x12\x11\n\rGender_FEMALE\x10\x02\x12\x15\n\x10Gender_UNLIMITED\x10\xe7\x07*l\n\nTimeOnline\x12\x13\n\x0fTimeOnline_NONE\x10\x00\x12\x16\n\x12TimeOnline_WORKDAY\x10\x01\x12\x16\n\x12TimeOnline_WEEKEND\x10\x02\x12\x19\n\x14TimeOnline_UNLIMITED\x10\xe7\x07*\x84\x01\n\nTimeActive\x12\x13\n\x0fTimeActive_NONE\x10\x00\x12\x16\n\x12TimeActive_MORNING\x10\x01\x12\x18\n\x14TimeActive_AFTERNOON\x10\x02\x12\x14\n\x10TimeActive_NIGHT\x10\x03\x12\x19\n\x14TimeActive_UNLIMITED\x10\xe7\x07*\x80\x01\n\nModePrefer\x12\x13\n\x0fModePrefer_NONE\x10\x00\x12\x11\n\rModePrefer_BR\x10\x01\x12\x11\n\rModePrefer_CS\x10\x02\x12\x1c\n\x18ModePrefer_ENTERTAINMENT\x10\x03\x12\x19\n\x14ModePrefer_UNLIMITED\x10\xe7\x07*X\n\x08RankShow\x12\x11\n\rRankShow_NONE\x10\x00\x12\x0f\n\x0bRankShow_BR\x10\x01\x12\x0f\n\x0bRankShow_CS\x10\x02\x12\x17\n\x12RankShow_UNLIMITED\x10\xe7\x07*R\n\tBadgeType\x12\x1a\n\x16\x42\x41\x44GE_TYPE_UNSPECIFIED\x10\x00\x12\x13\n\x0f\x42\x41\x44GE_TYPE_ROLE\x10\x01\x12\x14\n\x10\x42\x41\x44GE_TYPE_PRIME\x10\x02*m\n\nSparkState\x12\x13\n\x0fSparkState_NONE\x10\x00\x12\x15\n\x11SparkState_ACTIVE\x10\x01\x12\x16\n\x12SparkState_DORMANT\x10\x02\x12\x1b\n\x17SparkState_EXTINGUISHED\x10\x03\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'follow_pb2', _globals)

CSFollowReq = _globals['CSFollowReq']
CSFollowRes = _globals['CSFollowRes']

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
    urls = [
        "https://clientbp.ggpolarbear.com/Follow",        # BD Server
        "https://client.ind.freefiremobile.com/Follow"     # IND Server
    ]

    try:
        req = CSFollowReq()
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
                proto_res = CSFollowRes()
                proto_res.ParseFromString(res.content)
                return True, proto_res, ""
            elif res.status_code == 401:
                return False, None, "Token Expired (401)"
        except Exception:
            continue

    return False, None, "HTTP Server Error or Timeout"

# ==============================================================================
#                     SPIN.PY EXACT RESPONSE JUDGEMENT
# ==============================================================================
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

    # Check 1: Already Followed (✅ Saved)
    if "already" in fail_txt or "followed" in fail_txt:
        return {
            "uid": uid,
            "status": "already_followed",
            "result_type": "ALREADY_FOLLOWED",
            "message": "Already Followed (অলরেডি দেওয়া হয়ে গেছে)",
            "should_save": True
        }

    # Check 2: Fail Info from server (❌ NOT Saved - নষ্ট বা লিমিট শেষ হলে সরাসরি ফেইল্ড)
    if proto_res.fail_info:
        return {
            "uid": uid,
            "status": "failed",
            "result_type": "FAILED",
            "message": f"Failed: {proto_res.fail_info}",
            "should_save": False
        }

    # Check 3: MUST HAVE PLAYED 3 MAP MATCHES! (❌ NOT Saved)
    if hasattr(proto_res, 'remaining_play_count') and proto_res.remaining_play_count > 0:
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

# ==============================================================================
#                            SERVERLESS HANDLER
# ==============================================================================
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
        self._send_json(200, {
            "status": "online",
            "service": "Garena Follow Dispatcher v11.0 (Embedded Standalone Engine)",
            "proto_ready": True
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

            # Batch Follow Mode (একসাথে ৬০+ টোকেন ফায়ার হবে)
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
