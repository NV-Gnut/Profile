# Tổng quan và mục tiêu 

- Sử dụng trình phân tích IDA ở phần cuối trang có thể thấy file smiles này đã bị nén bởi upx, việc phân tích file nén sẽ khó khăn vậy nên chúng ta sẽ đi khôi phục lại file 
<img width="998" height="100" alt="Screenshot 2025-08-25 110737" src="https://github.com/user-attachments/assets/3aaab8c4-855e-48e1-a35b-f6c61b3fd3e7" />

- Sau khi khôi phục thì tiến hành phân tích . Từ hàm main sẽ gọi hàm run_chemistry_quiz sau đó sẽ gọi run_password_checker.
<img width="1250" height="713" alt="Screenshot 2025-08-25 111324" src="https://github.com/user-attachments/assets/3c8ffaf5-85a4-4c58-afd8-d6d8c268015c" />

- Đi sâu vào phân tích hàm run_chemistry_quiz :
+ Thứ nhất là hàm sẽ kiểm tra 5 questions và kiểm tra bằng cách so sánh phần từ của mảng aAhoh với v2
+ Thứ hai là sau khi trả lời đúng thì sẽ tiến hành nối chuỗi questions vào chuỗi a1
<img width="765" height="756" alt="Screenshot 2025-08-25 111933" src="https://github.com/user-attachments/assets/75d946e3-d24a-42a4-9798-4665eb44b22e" />

- phân tích hàm run_password_checker:
+ đầu tiên là encode_message dữ liệu s (password người dùng nhập vào) và chuỗi a1 từ hàm run_chemistry_quiz
+ Sau đó sẽ đem đi so sánh với chuỗi mẫu và in ra 'success' nếu khớp và 'failed' nếu không khớp
<img width="1348" height="743" alt="Screenshot 2025-08-25 112936" src="https://github.com/user-attachments/assets/97f12045-e2b0-4806-91d2-f03a58f08374" />


-> Flag sẽ chính là chuỗi password s 

# Phân tích 

- Cần xác định được chuỗi a1 trong hàm run_chemistry_quiz 
- Phân tích hàm encode_message :
 <img width="909" height="612" alt="Screenshot 2025-08-25 114548" src="https://github.com/user-attachments/assets/76de1513-d4a8-4bb7-beba-10f6424e6e2f" />
+ nó sẽ tạo hoán vị chuỗi a1  bằng cách tạo seed v4  bởi hàm hash_molecular_key(a1) sau đó sẽ v4 nhân với hằng số 16807 và lấy dư với 0x7FFFFFFF (tức 2^31 - 1), tạo ra một dãy số giả ngẫu nhiên lưu vào v9 
<img width="732" height="291" alt="Screenshot 2025-08-25 120928" src="https://github.com/user-attachments/assets/25a84bbc-1574-4bcb-bdb7-a6f139b77311" />
<img width="394" height="143" alt="Screenshot 2025-08-25 120954" src="https://github.com/user-attachments/assets/3fa493b0-1e2d-42c7-857d-9588b670ae3c" />

+ đoạn code tiếp theo sẽ ánh xạ mỗi ký tự a1 sang một chuỗi tương tức trong mảng MOLECULE_DB dựa trên bảng hoán vị v9 
<img width="682" height="315" alt="Screenshot 2025-08-25 152706" src="https://github.com/user-attachments/assets/0ef08d5a-7c13-4600-a253-62432a8bb1b0" />


(mảng MOLECULE_DB )
<img width="856" height="715" alt="Screenshot 2025-08-25 152928" src="https://github.com/user-attachments/assets/4358171f-56aa-47fc-af76-db7a342156ed" />


# KẾT QUẢ
📎[[script.py]](https://github.com/NV-Gnut/CTF-Write-Up/blob/main/DDC%20CTF/REV/script.py)
Flag: DDC{1_gu3s5_u_n3v4_7hought_0f_7h1s_ch3m1stry_3ncrypt1on}


