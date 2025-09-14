"""
Face detection threshold configuration
Lower thresholds to make it easier to check dynamic and static images
"""

# Pose Detection (Face tilt angle) - Increase threshold to make it easier
POSE_MAX_YAW = 60.0      # Left/right tilt angle (increased from 50.0)
POSE_MAX_PITCH = 55.0    # Up/down tilt angle (increased from 45.0)
POSE_MAX_ROLL = 55.0     # Rotation angle (increased from 45.0)

# Quality Detection (Image quality) - Lower threshold to make it easier
QUALITY_MIN_SHARPNESS = 0.12  # Minimum sharpness (lowered from 0.18)
QUALITY_MIN_EXPOSURE = 0.15   # Minimum brightness (lowered from 0.25)
QUALITY_MIN_AREA = 0.05       # Minimum face area (lowered from 0.08)

# Liveness Detection (Real person detection) - Lower threshold to make it easier
LIVENESS_MIN_SCORE = 0.02     # Minimum liveness threshold (lowered from 0.05)
LIVENESS_TOLERANCE = 0.15     # Liveness tolerance (increased from 0.10)

# Mask Detection (Mask detection) - Increase threshold to detect masks more strictly
MASK_CONF_THRESHOLD = 0.5     # Mask detection threshold (lowered from 0.7 to detect easier)
MASK_SKIN_RATIO_THRESHOLD = 0.25  # Skin ratio threshold (increased from 0.15 to detect easier)
MASK_CONSECUTIVE_FRAMES = 3   # Number of consecutive frames to confirm mask (lowered from 5 to detect faster)

# Video Processor Thresholds
READINESS_THRESHOLD = 0.05    # Ready to capture image threshold (lowered from 0.1)
MOTION_FRAMES_REQUIRED = 2    # Number of motion frames required (lowered from 3)

# Face Comparison Thresholds - Increase threshold to check face matching more strictly
FACE_SIMILARITY_THRESHOLD = 0.8  # Face comparison threshold (increased from 0.6 to 0.8)

# Feature Flags
ENABLE_QUALITY = True
ENABLE_POSE = True
ENABLE_LIVENESS = True
ENABLE_MASK = True
BLOCK_STRICT = True

# Debug Mode - Enable to see detailed processing
DEBUG_MODE = True
