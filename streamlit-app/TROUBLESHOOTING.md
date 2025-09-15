# 🔧 Troubleshooting Guide

## Camera Issues

### 1. Camera không hiển thị
**Triệu chứng:** Camera không xuất hiện hoặc hiển thị thông báo lỗi

**Giải pháp:**
- Kiểm tra quyền truy cập camera trong browser
- Đảm bảo không có ứng dụng nào khác đang sử dụng camera
- Thử refresh trang (F5)
- Kiểm tra camera có hoạt động bình thường không

### 2. Camera bị lag hoặc chậm
**Triệu chứng:** Video bị giật lag, xử lý chậm

**Giải pháp:**
- Đóng các tab browser khác
- Kiểm tra CPU usage
- Giảm độ phân giải camera
- Restart browser

### 3. Face detection không hoạt động
**Triệu chứng:** Không phát hiện được khuôn mặt

**Giải pháp:**
- Đảm bảo ánh sáng đủ
- Đặt khuôn mặt ở giữa khung hình
- Loại bỏ kính mắt, khẩu trang
- Kiểm tra camera có bị mờ không

## Service Issues

### 1. FaceID Service offline
**Triệu chứng:** Lỗi khi encode face hoặc compare faces

**Giải pháp:**
```bash
cd faceid-service
python app.py
```

### 2. User Service offline
**Triệu chứng:** Lỗi khi đăng ký hoặc điểm danh

**Giải pháp:**
```bash
cd user-service
python run.py
```

### 3. API connection errors
**Triệu chứng:** Timeout hoặc connection refused

**Giải pháp:**
- Kiểm tra ports: 5000 (FaceID), 5002 (User)
- Kiểm tra firewall settings
- Restart services

## Browser Issues

### 1. WebRTC không hoạt động
**Triệu chứng:** Camera không load được

**Giải pháp:**
- Sử dụng HTTPS hoặc localhost
- Kiểm tra browser compatibility
- Thử browser khác (Chrome, Firefox, Edge)

### 2. Permission denied
**Triệu chứng:** Browser từ chối truy cập camera

**Giải pháp:**
- Click vào icon camera trên address bar
- Allow camera access
- Clear browser cache và cookies

## Performance Issues

### 1. App chạy chậm
**Giải pháp:**
- Đóng các tab không cần thiết
- Restart browser
- Kiểm tra RAM usage
- Sử dụng camera đơn giản thay vì WebRTC

### 2. Memory issues
**Giải pháp:**
- Restart Streamlit app
- Clear browser cache
- Kiểm tra memory usage

## Testing Steps

### 1. Test Camera
1. Vào trang "Camera Test"
2. Click "Start Camera"
3. Click "Capture Photo"
4. Kiểm tra ảnh có hiển thị không

### 2. Test Services
1. Vào trang "Camera Test"
2. Click "Check FaceID Service"
3. Click "Check User Service"
4. Đảm bảo cả 2 đều online

### 3. Test Face Detection
1. Chụp ảnh rõ nét
2. Click "Test Face Detection"
3. Kiểm tra kết quả

## Common Error Messages

### "Camera not detected"
- Kiểm tra camera permissions
- Restart browser
- Thử camera khác

### "Face encoding failed"
- Kiểm tra FaceID service
- Đảm bảo ảnh có khuôn mặt rõ nét
- Thử lại

### "Service offline"
- Start backend services
- Kiểm tra ports
- Kiểm tra firewall

## Contact Support

Nếu vấn đề vẫn chưa được giải quyết:
1. Ghi lại error message
2. Chụp screenshot
3. Mô tả steps để reproduce
4. Liên hệ support team
