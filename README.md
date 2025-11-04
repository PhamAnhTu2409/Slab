# 🔬 SlabMaker Web App - Hướng dẫn cài đặt và chạy trên Windows

## 📋 Giới thiệu

SlabMaker là ứng dụng web tạo surface từ cấu trúc tinh thể, hỗ trợ nhiều
định dạng file đầu vào (POSCAR, CIF, Quantum ESPRESSO).

## 🏗️ Cấu trúc dự án

    slabmaker-web/
    ├── backend/          # Python Flask API
    │   ├── app.py
    │   ├── cell.py
    │   ├── cif_parser.py
    │   └── requirements.txt
    ├── frontend/         # Giao diện web
    │   ├── index.html
    │   ├── style.css
    │   └── script.js
    └── README.md

## ⚙️ Yêu cầu hệ thống

-   Windows 10/11\
-   Python 3.8+\
-   Trình duyệt web (Chrome, Firefox, Edge)

------------------------------------------------------------------------

## 🚀 Cài đặt và chạy Backend

### ✅ Bước 1: Tải và cài đặt Python

-   Truy cập https://python.org
-   Tải Python 3.8+ cho Windows
-   **Quan trọng**: tick vào "Add Python to PATH"
-   Hoàn tất cài đặt

### ✅ Bước 2: Kiểm tra Python

Mở Command Prompt (Win + R → `cmd`):

``` bash
python --version
pip --version
```

### ✅ Bước 3: Cài đặt Backend

Mở Command Prompt **Run as Administrator** và chuyển đến thư mục
backend:

``` bash
cd \backend
pip install -r requirements.txt
```

Nếu lỗi, chạy:

``` bash
python -m pip install --upgrade pip
pip install flask==2.3.3 flask-cors==4.0.0 numpy==1.24.3 f90nml==1.4.1
```

### ✅ Bước 4: Chạy Backend Server

``` bash
python app.py
```

Kết quả:

    * Running on http://127.0.0.1:5000

> Giữ cửa sổ CMD mở --- đây là server backend.

------------------------------------------------------------------------

## 🌐 Chạy Frontend

### ✅ Cách 1: Mở trực tiếp file

-   Mở thư mục `frontend`
-   Double-click `index.html`

### ✅ Cách 2: Dùng Live Server (VSCode)

-   Cài extension **Live Server**
-   Mở thư mục project
-   Right-click `index.html` → `Open with Live Server`

### ✅ Cách 3: Python HTTP Server

``` bash
cd \frontend
python -m http.server 8000
```

Truy cập: http://localhost:8000

------------------------------------------------------------------------

## 🎯 Kiểm tra hoạt động

  Thành phần   Địa chỉ
  ------------ -----------------------
  Backend      http://localhost:5000
  Frontend     http://localhost:8000

Test kết nối bằng cách upload file và tạo surface

------------------------------------------------------------------------

## 📁 Cấu hình mạng (Firewall)

-   Mở Windows Security → Firewall
-   Allow app through firewall → chọn `python.exe` (Private + Public)

------------------------------------------------------------------------

## 🐛 Xử lý lỗi thường gặp

  Lỗi                Cách sửa
  ------------------ ---------------------------------------------
  Python not found   Cài lại và tick "Add to PATH"
  Module not found   `pip install numpy flask flask-cors f90nml`
  Port 5000 in use   Đóng app khác hoặc đổi port
  CORS error         Cài flask-cors và kiểm tra backend

------------------------------------------------------------------------

## 🔧 Script tự động chạy (Tùy chọn)

Tạo `start.bat`:

``` bat
@echo off
echo Starting SlabMaker Web App...
cd backend
start python app.py
timeout /t 3
cd ..\frontend
start index.html
echo App started! Backend: http://localhost:5000
pause
```

Double-click `start.bat` để chạy cả backend & frontend.

------------------------------------------------------------------------

## 🎉 Khi thành công

-   Backend chạy tại **http://localhost:5000**
-   Frontend mở trong trình duyệt
-   Có thể upload file và tạo surface

**Chúc bạn sử dụng SlabMaker thành công! 🚀**
