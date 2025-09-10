# API xử lý khuôn mặt: /api/encode-face, /api/compare-faces
# Gợi ý đơn giản: dùng OpenCV đọc ảnh, sinh embedding giả lập (mean pixel) cho demo.
from flask import Blueprint, request, jsonify
import numpy as np
import cv2
from ..utils.preprocessing import read_image_bytes

face_bp = Blueprint("face_api", __name__)

def _dummy_embed(img: np.ndarray) -> list[float]:
    # Demo: vector 128 chiều = thống kê pixel (KHÔNG dùng cho production)
    # Thực tế: thay bằng model DL (FaceNet, ArcFace, v.v.)
    vec = np.concatenate([
        [float(img.mean())],
        img.mean(axis=0).mean(axis=0).tolist() if img.ndim == 3 else [float(img.mean())]*3
    ])
    # pad về 128 chiều
    if vec.shape[0] < 128:
        vec = np.pad(vec, (0, 128 - vec.shape[0]))
    return vec[:128].astype(float).tolist()

@face_bp.route("/encode-face", methods=["POST"])
def encode_face():
    # Nhận file ảnh: form field "file"
    if "file" not in request.files:
        return jsonify({"error": "Thiếu file ảnh (field 'file')"}), 400
    file = request.files["file"]
    img = read_image_bytes(file.read())
    if img is None:
        return jsonify({"error": "Ảnh không hợp lệ"}), 400

    emb = _dummy_embed(img)
    return jsonify({"embedding": emb})

@face_bp.route("/compare-faces", methods=["POST"])
def compare_faces():
    # JSON: {"emb1":[...], "emb2":[...]}
    data = request.get_json(silent=True) or {}
    emb1 = np.array(data.get("emb1", []), dtype=float)
    emb2 = np.array(data.get("emb2", []), dtype=float)
    if emb1.size == 0 or emb2.size == 0 or emb1.shape != emb2.shape:
        return jsonify({"error": "Thiếu hoặc sai định dạng embedding"}), 400

    # khoảng cách cosine (1-cosine similarity)
    def cosine_dist(a, b):
        denom = (np.linalg.norm(a) * np.linalg.norm(b))
        if denom == 0: return 1.0
        return float(1 - (a @ b) / denom)

    dist = cosine_dist(emb1, emb2)
    # Ngưỡng demo: < 0.3 coi như cùng người (tuỳ chỉnh theo model thực tế)
    return jsonify({"distance": dist, "match": dist < 0.3})
