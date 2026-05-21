# Challenge Overview
Object: Thực hiện khai thác lỗ hổng Path traversal để đọc nội dung file /etc/passwd sau đó giải mã đoạn comment để nhận Flag
# Solution Plan
1. Truy cập vào source mình phát hiện có endpoint dạng `?url=forms\`
2. Trong index.php có hiện thị các thư mục forms\servers-status.txt ,.. . Qua đó mình xác định được endpoint đó sẽ thực hiện đọc nội dung của file => Lỗ hổng path traversal
3. Thử `?url=forms/../../../../etc/passwd` => Response:  Not find file. Quay trở lại cái mô tả và hint tác giả đã cung cấp, nếu request được gửi từ một nguồn tin cậy thì response sẽ phản hồi khác
4. Mình thêm header `X-Forwarder-For: 2130706433`
   ```
   curl -H "X-Forwarder-For:2130706433" https://challenge.com?url=forms/../../../../../etc/passwd
   ```   
5. Mình sẽ nhận được đoạn mã ở phần comment. Đoạn mã đó là dạng pigpen. Thực hiện giải mã sẽ ra flag
# FLAG
~~`0xV10D{PIGPEN_CIPTHER_GOOD_JOB}`~~