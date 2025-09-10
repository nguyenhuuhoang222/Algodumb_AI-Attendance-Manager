# Kiến trúc tổng quan

- `faceid-service`: sinh embedding và so khớp
- `user-service`: gọi faceid-service, lưu user+embedding
- `streamlit-app`: UI gọi user-service

Luồng chính:
1. Đăng ký: UI -> user-service `/register-face` -> gọi faceid-service `/encode-face` -> lưu DB
2. Đăng nhập: UI -> user-service `/login-face` -> gọi faceid-service `/encode-face` + `/compare-faces` -> trả kết quả
