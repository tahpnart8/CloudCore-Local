# Engineering Log 02: Provisioning Infrastructure as Code (Terraform)

## 1. Mục tiêu kỹ thuật
Với tư duy của một Cloud Engineer, việc tạo hạ tầng bằng tay (click giao diện hoặc gõ từng lệnh CLI rời rạc) là một "anti-pattern". Mục tiêu của tôi trong phase này là phải code hóa toàn bộ quy trình tạo cụm Kubernetes thành các file cấu hình (Infrastructure as Code - IaC) bằng **Terraform**, đảm bảo khả năng tái tạo hạ tầng (reproducibility) với độ trễ (MTTR) thấp nhất.

## 2. Quá trình thực thi

Tôi thiết kế hạ tầng gồm:
- 1 Server Node (Control Plane): Đóng vai trò quản lý cụm.
- 1 Agent Node (Worker Node): Đóng vai trò xử lý các tác vụ nặng (Chạy Database, Streaming, AI).
- 1 Load Balancer (chạy cổng 80 và 443) map trực tiếp ra môi trường Localhost.

### Code Terraform
- Khởi tạo thư mục `terraform/` với file `main.tf`.
- Sử dụng provider `kreuzwerker/docker` để tương tác với Docker daemon.
- Khai báo block `docker_network` để tạo mạng lưới nội bộ cho cụm.
- Thay vì dùng bash script chạy `k3d cluster create`, tôi nhúng lệnh này vào `null_resource` với provisioner `local-exec` của Terraform để tự động hóa hoàn toàn. Lệnh tạo cluster đi kèm các tham số tối ưu:
  - `--agents 1`: Cấp phát 1 node worker.
  - `-p "80:80@loadbalancer"`: Port mapping cho ingress.
  - `--k3s-arg "--disable=traefik@server:0"`: Tắt Traefik mặc định để tiết kiệm RAM.

## 3. Trục trặc gặp phải & Cách giải quyết (Troubleshooting)

**Vấn đề:** Không thể chạy `terraform init` hoặc cluster không tạo thành công do thiếu plugin.
*Nguyên nhân:* Môi trường Terraform không nhận dạng được Docker socket hoặc provider bị thiếu phiên bản tương thích.
*Cách giải quyết:* 
Tôi đã cấu hình lại file `main.tf`, xác định rõ block `required_providers` với phiên bản cụ thể (`kreuzwerker/docker ~> 3.0.1`). Đồng thời, khi gỡ lỗi (debug) quá trình tạo cụm k3d, tôi phát hiện cần thêm lệnh dọn dẹp `k3d cluster delete` vào block `destroy` của provisioner để đảm bảo Terraform có thể dọn dẹp sạch sẽ hạ tầng cũ trước khi tạo mới (Idempotency).

## 4. Kết quả (Outcome)
Hệ thống đạt tiêu chuẩn IaC hoàn hảo. Bây giờ, bất kỳ lúc nào muốn xây lại toàn bộ cụm Kubernetes đa node (Multi-node cluster), tôi chỉ cần chạy duy nhất 1 lệnh:
`terraform apply -auto-approve`
Và toàn bộ Data Center giả lập sẽ được dựng lên hoàn chỉnh **chỉ trong vòng 3 phút!**
