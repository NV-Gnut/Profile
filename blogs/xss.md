# Lỗ hổng XSS là gì ?
XSS là một lỗ hổng bảo mật web. Lỗ hổng này cho phép kẻ tấn công tiêm đoạn script độc hại phía client vào một trang web đáng tin cậy. Những script độc hại đó sẽ được thực thi trong trình duyệt của nạn nhân và được chạy với cùng quyền hạn của javascript của website được phép sử dụng. 
# Ảnh hưởng của XSS?
Những rủi ro có thể xảy ra khi attacker khai thác lỗ hổng XSS:
- Đánh cắm cookies.
- Chiếm quyền kiểm soát người dùng
- Thực hiện người dùng như một người dùng khác
- Thay đổi giao diện trang web
- Chuyển hướng người dùng tới malicious websites
- Phát tán mã độc hoặc các trang web lừa đảo

# Các bước diễn ra trong một cuộc tấn công XSS
1. Kẻ tấn công tiêm đoạn mã độc javascript vào trường input có lỗ hổng
2. Ứng dụng web có thể lưu trữ và phản hồi đoạn payload đó mà không lọc đúng cách
3. Người dùng khác truy cập vào trang bị ảnh hưởng
4. Trình duyệt sẽ thực hiện đoạn script đã được tiêm vào như là một đoạn code hợp pháp

# Các loại XSS
Hiện nay, có 3 loại XSS phổ biến (Reflected, Stored, DOM). Trong thực tế thì chúng bị chồng chéo lên nhau. Để làm rõ và tránh nhầm lẫn thì một cộng đồng nghiên cứu đã đề suất việc sử dụng 2 khái niệm mới để giúp sắp xếp các loại XSS có thể xảy ra: Server XSS và Client XSS.


1. Reflected XSS

