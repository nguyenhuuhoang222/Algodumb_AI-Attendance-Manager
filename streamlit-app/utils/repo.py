# streamlit-app/utils/repo.py
import json, glob, os
from typing import List, Dict, Any, Optional, Tuple
import requests
import streamlit as st

def _base_url() -> str:
    return st.secrets.get("USER_SERVICE_URL", "http://localhost:5002/api").rstrip("/")

def _safe_get(url: str, params=None) -> Optional[Dict]:
    try:
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

def _safe_post(url: str, data=None, json_data=None, files=None) -> Optional[Dict]:
    try:
        r = requests.post(url, data=data, json=json_data, files=files, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

# ---------- Fallback local JSON ----------
_ROOT = os.path.dirname(os.path.dirname(__file__))
_USERS_DIR = os.path.join(_ROOT, "tests", "json", "users")
_ATT_DIR   = os.path.join(_ROOT, "tests", "json", "attendance_records")

def _read_many_json(dir_path: str) -> List[Dict]:
    def _flatten(x):
        if isinstance(x, list):
            out = []
            for i in x:
                out.extend(_flatten(i))
            return out
        if isinstance(x, dict):
            for k in ["items", "data", "records", "result", "rows"]:
                if k in x and isinstance(x[k], (list, dict)):
                    return _flatten(x[k])
            return [x]
        return []
    out = []
    for fp in sorted(glob.glob(os.path.join(dir_path, "*.json"))):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
                out.extend(_flatten(data))
        except Exception:
            pass
    return out


# ---------- Public API ----------
def list_users(search: str = "", status: str = "", page: int = 1, size: int = 5) -> Tuple[List[Dict], int]:
    """Trả về (items, total). status để dành nếu backend có."""
    url = f"{_base_url()}/users"
    payload = _safe_get(url, params={"q": search, "status": status, "page": page, "size": size}) 
    if payload and isinstance(payload, dict) and "items" in payload:
        return payload["items"], int(payload.get("total", len(payload["items"])))
    # fallback
    data = _read_many_json(_USERS_DIR)
    if search:
        data = [x for x in data if search.lower() in str(x.get("name","")).lower()]
    total = len(data)
    start = (page-1)*size
    return data[start:start+size], total

def create_user(user: Dict[str, Any]) -> Dict:
    """Gọi API tạo user; fallback chỉ echo."""
    url = f"{_base_url()}/users"
    resp = _safe_post(url, json_data=user)
    return resp or {"_mock": True, **user}

def list_attendance(search: str = "", status: str = "", page: int = 1, size: int = 5):
    url = f"{_base_url()}/attendance"
    payload = _safe_get(url, params={"q": search, "status": status, "page": page, "size": size})
    if payload and isinstance(payload, dict) and "items" in payload:
        return payload["items"], int(payload.get("total", len(payload["items"])))

    # ---------- Fallback local ----------
    data = _read_many_json(_ATT_DIR)
    users = _read_many_json(_USERS_DIR)

    # map id -> user
    by_id = {}
    for u in users:
        uid = u.get("id") or u.get("user_id") or u.get("code")
        if uid is not None:
            by_id[str(uid)] = u

    def enrich(a: Dict[str, Any]) -> Dict[str, Any]:
        uid = a.get("user_id") or a.get("userId") or (a.get("user") or {}).get("id")
        if not a.get("user_name"):
            name = (a.get("user") or {}).get("name")
            if not name and uid is not None and str(uid) in by_id:
                name = by_id[str(uid)].get("name")
            if name:
                a["user_name"] = name
        if not a.get("captured_image"):
            if uid is not None and str(uid) in by_id:
                a["image_path"] = a.get("image_path") or by_id[str(uid)].get("image_path") or by_id[str(uid)].get("avatar")
        return a

    data = [enrich(row) for row in data]

    if search:
        kw = search.lower()
        def _name(a):
            return (a.get("user_name")
                    or a.get("name")
                    or (a.get("user") or {}).get("name")
                    or "")
        data = [a for a in data if kw in _name(a).lower()]

    if status:
        data = [a for a in data if str(a.get("status","")).lower() == status.lower()]

    total = len(data)
    start = (page-1)*size
    return data[start:start+size], total

def stats() -> Dict[str, int]:
    url = f"{_base_url()}/stats"
    payload = _safe_get(url)
    if isinstance(payload, dict) and any(k in payload for k in ["users","attendance","present","absent"]):
        return payload

    all_users = _read_many_json(_USERS_DIR)
    all_att = _read_many_json(_ATT_DIR)

    def _norm_status(s: Any) -> str:
        s = str(s or "").strip().lower()
        # map variant present/absent
        aliases = {
            "present": {"present","in","checked_in","on-time","on_time","attend"},
            "absent":  {"absent","off","no-show","noshow","miss","away"},
        }
        for key, vals in aliases.items():
            if s in vals:
                return key
        return s  

    present = absent = 0
    for x in all_att:
        stt = _norm_status(x.get("status"))
        if stt == "present": present += 1
        elif stt == "absent": absent += 1

    return {
        "users": len(all_users),
        "attendance": len(all_att),
        "present": present,
        "absent": absent
    }

def login_password(username: str, password: str) -> Dict[str, Any]:
    """POST /auth/login -> {ok, data|error}"""
    url = f"{_base_url()}/auth/login"
    try:
        resp = requests.post(url, json={"username": username, "password": password}, timeout=10)
        if resp.ok:
            return {"ok": True, "data": resp.json()}
        return {"ok": False, "error": resp.text or "Login failed"}
    except Exception as ex:
        return {"ok": False, "error": str(ex)}

def login_face(image_bytes: bytes) -> Dict[str, Any]:
    """POST /auth/face-login (multipart) -> {ok, data|error}"""
    url = f"{_base_url()}/auth/face-login"
    try:
        files = {"image": ("capture.jpg", image_bytes, "image/jpeg")}
        resp = requests.post(url, files=files, timeout=10)
        if resp.ok:
            return {"ok": True, "data": resp.json()}
        return {"ok": False, "error": resp.text or "Face login failed"}
    except Exception as ex:
        return {"ok": False, "error": str(ex)}

def submit_attendance(image_bytes: bytes) -> Dict[str, Any]:
    """POST /attendance/checkin (multipart) -> {ok, data|error}"""
    url = f"{_base_url()}/attendance/checkin"
    try:
        files = {"image": ("attendance.jpg", image_bytes, "image/jpeg")}
        resp = requests.post(url, files=files, timeout=10)
        if resp.ok:
            return {"ok": True, "data": resp.json()}
        return {"ok": False, "error": resp.text or "Submit failed"}
    except Exception as ex:
        return {"ok": False, "error": str(ex)}
