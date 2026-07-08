# Engineering Log 01: Khởi tạo Môi trường Hạ tầng (Environment Setup)

## 1. Mục tiêu kỹ thuật
Để giả lập một môi trường Cloud-Native chân thực nhất trên máy tính cá nhân (Windows 11), tôi cần một lớp nhân Linux (Linux Kernel) thực thụ. Giải pháp tối ưu nhất là sử dụng kết hợp **WSL2 (Windows Subsystem for Linux)** và **Docker Desktop**.

Việc cài đặt này không chỉ đơn thuần là "Next -> Next -> Finish", mà cốt lõi là việc cấp quyền và thiết lập cầu nối mạng (network bridge) giữa Windows host và Docker daemon chạy ngầm trong WSL2.

## 2. Quá trình thực thi

### Thiết lập WSL2 & Docker Desktop
- Tôi cài đặt WSL2 với bản phân phối Ubuntu mặc định để có môi trường gõ lệnh Linux chuẩn.
- Cài đặt Docker Desktop và kích hoạt tính năng **WSL 2 based engine**. Đây là bước quan trọng nhất: nó cho phép Docker daemon chạy trực tiếp trên nhân Linux của WSL2 thay vì phải tạo một máy ảo Hyper-V cồng kềnh, giúp tối ưu hóa hiệu suất CPU và RAM đáng kể.
- Kích hoạt **Docker integration** cho distro Ubuntu trong cài đặt Docker Desktop, đảm bảo tôi có thể gọi lệnh `docker` trực tiếp từ terminal của Ubuntu.

### Cài đặt Công cụ CLI (Command Line Interface)
Tôi đã viết một bash script tự động hóa để cài đặt các công cụ cần thiết vào WSL:
- `kubectl`: Giao tiếp với Kubernetes cluster.
- `helm`: Quản lý các package/deployment trên Kubernetes.
- `terraform`: Tự động hóa hạ tầng (IaC).
- `ansible`: Quản lý cấu hình (Configuration Management).
- `k3d`: Trình bao bọc (wrapper) để chạy Kubernetes (k3s) bên trong các Docker containers.

## 3. Trục trặc gặp phải & Cách giải quyết (Troubleshooting)

**Vấn đề:** Không thể kết nối từ Windows vào các dịch vụ chạy trong WSL/Docker qua localhost.
*Bối cảnh:* Khi chạy một số container thử nghiệm, truy cập `localhost` từ trình duyệt Windows đôi khi bị lỗi "Connection Refused".
*Nguyên nhân Root Cause:* Lỗi cấu hình mạng của WSL2 (NAT network) khiến Windows không thể resolve đúng IP của container. Ngoài ra, việc quên cấp quyền chạy script (`chmod +x`) cũng làm gián đoạn quá trình cài đặt tool.
*Cách giải quyết:* 
1. Sử dụng lệnh `chmod +x install_tools.sh` trước khi thực thi.
2. Thiết lập IP Binding cẩn thận trong các bước sau (sử dụng `0.0.0.0` thay vì `127.0.0.1` bên trong container) để đảm bảo các dịch vụ lắng nghe trên mọi network interface, cho phép WSL2 map port thành công ra ngoài Windows host.

## 4. Kết quả (Outcome)
Môi trường Ubuntu hoàn toàn sạch sẽ, nhẹ nhàng và đã được trang bị đầy đủ "vũ khí" (CLI tools) để sẵn sàng bước vào giai đoạn Provisioning kiến trúc K8s phân tán.
