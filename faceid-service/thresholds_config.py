"""
Cấu hình ngưỡng phát hiện khuôn mặt
Hạ ngưỡng để dễ dàng kiểm tra ảnh động và tĩnh
"""

# Pose Detection (Góc nghiêng khuôn mặt) - Tăng ngưỡng để dễ dàng hơn
POSE_MAX_YAW = 60.0      # Góc nghiêng trái/phải (tăng từ 50.0)
POSE_MAX_PITCH = 55.0    # Góc nghiêng lên/xuống (tăng từ 45.0)
POSE_MAX_ROLL = 55.0     # Góc xoay (tăng từ 45.0)

# Quality Detection (Chất lượng ảnh) - Hạ ngưỡng để dễ dàng hơn
QUALITY_MIN_SHARPNESS = 0.12  # Độ sắc nét tối thiểu (hạ từ 0.18)
QUALITY_MIN_EXPOSURE = 0.15   # Độ sáng tối thiểu (hạ từ 0.25)
QUALITY_MIN_AREA = 0.05       # Diện tích khuôn mặt tối thiểu (hạ từ 0.08)

# Liveness Detection (Phát hiện người thật) - Hạ ngưỡng để dễ dàng hơn
LIVENESS_MIN_SCORE = 0.02     # Ngưỡng liveness tối thiểu (hạ từ 0.05)
LIVENESS_TOLERANCE = 0.15     # Tolerance cho liveness (tăng từ 0.10)

# Mask Detection (Phát hiện khẩu trang) - Tăng ngưỡng để phát hiện khẩu trang chặt chẽ hơn
MASK_CONF_THRESHOLD = 0.5     # Ngưỡng phát hiện khẩu trang (hạ từ 0.7 để phát hiện dễ hơn)
MASK_SKIN_RATIO_THRESHOLD = 0.25  # Ngưỡng tỷ lệ da (tăng từ 0.15 để phát hiện dễ hơn)
MASK_CONSECUTIVE_FRAMES = 3   # Số frame liên tiếp để xác nhận mask (hạ từ 5 để phát hiện nhanh hơn)

# Video Processor Thresholds
READINESS_THRESHOLD = 0.05    # Ngưỡng sẵn sàng chụp ảnh (hạ từ 0.1)
MOTION_FRAMES_REQUIRED = 2    # Số frame motion cần thiết (hạ từ 3)

# Face Comparison Thresholds - Tăng ngưỡng để kiểm tra trùng mặt chặt chẽ hơn
FACE_SIMILARITY_THRESHOLD = 0.8  # Ngưỡng so sánh khuôn mặt (tăng từ 0.6 lên 0.8)

# Feature Flags
ENABLE_QUALITY = True
ENABLE_POSE = True
ENABLE_LIVENESS = True
ENABLE_MASK = True
BLOCK_STRICT = True

# Debug Mode - Bật để xem chi tiết quá trình xử lý
DEBUG_MODE = True
