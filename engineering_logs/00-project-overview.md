# Engineering Log 00: Tổng Quan Dự Án & Quyết Định Kiến Trúc

## 1. Giới thiệu bài toán (The Business Problem)
Với sự phát triển bùng nổ của E-commerce, dữ liệu hành vi người dùng (click, view, cart, purchase) được sinh ra với tốc độ khổng lồ. Yêu cầu đặt ra cho các hệ thống hiện đại không chỉ là khả năng chịu tải cao, mà còn phải phản hồi theo thời gian thực (real-time) để đưa ra các gợi ý sản phẩm phù hợp ngay lập tức, từ đó tăng tỷ lệ chuyển đổi (Conversion Rate).

Dự án **CloudCore** được tôi thiết kế và phát triển để giải quyết bài toán này. Đây là một nền tảng phân tích luồng sự kiện (Event Streaming) và gợi ý AI thời gian thực, tuân thủ nghiêm ngặt các tiêu chuẩn kiến trúc Cloud-Native.

## 2. Quyết định Kiến trúc (Architectural Decisions)

Thay vì phụ thuộc vào các dịch vụ Managed Services đắt đỏ của AWS hay Google Cloud, tôi quyết định tự tay xây dựng tầng lõi (Core Infrastructure) ngay trên môi trường local (WSL2/Docker). Quyết định này mang lại hai lợi thế lớn:
1. **Tiết kiệm chi phí hoàn toàn:** Một cụm Kubernetes tương đương trên Cloud có thể tốn hàng trăm USD mỗi tháng.
2. **Làm chủ công nghệ lõi:** Tự tay xử lý các vấn đề về phân bổ tài nguyên, cấp phát mạng (networking), và bảo mật OS. Bất kỳ lúc nào cần, kiến trúc này có thể dễ dàng "Lift and Shift" lên môi trường Production thực tế nhờ tính chất Infrastructure-as-Code.

### Các công nghệ cốt lõi được lựa chọn:
* **Hạ tầng (Infrastructure):** Kubernetes (K3d/K3s) thay vì Minikube để giả lập chân thực kiến trúc Multi-node (1 Server, 1 Agent).
* **Tự động hóa (IaC & Config Management):** Terraform để cấp phát tài nguyên hạ tầng trong 3 phút, và Ansible để tự động hóa cấu hình bảo mật OS (OS Hardening).
* **Streaming Engine:** Redpanda (Kafka-compatible) được chọn vì nó nhẹ, viết bằng C++, không cần Zookeeper, cực kỳ phù hợp để chạy local nhưng vẫn đảm bảo throughput khổng lồ.
* **AI Service:** FastAPI kết hợp Milvus (Vector DB) và mô hình `all-MiniLM-L6-v2` để xử lý gợi ý sản phẩm dựa trên vector ngữ nghĩa.
* **Observability (Giám sát):** Prometheus, Grafana và Alertmanager để theo dõi sức khỏe hệ thống và mô phỏng các kịch bản phản ứng sự cố (Incident Response).

## 3. Tổng kết quy trình (The Roadmap)
Quá trình xây dựng dự án được tôi chia làm 6 giai đoạn (Phases) rõ rệt, áp dụng tư duy phát triển phần mềm Agile và SRE (Site Reliability Engineering):
1. Thiết lập Cụm Kubernetes bằng Terraform.
2. Tăng cường bảo mật (Hardening) bằng Ansible.
3. Container hóa và Deploy dịch vụ AI Vector Recommendation.
4. Triển khai Streaming Pipeline xử lý 4.1 triệu sự kiện E-commerce.
5. Thiết lập hệ thống Giám sát toàn diện (Observability).
6. Diễn tập Sự cố Production (Chaos Engineering).

Trong các file log tiếp theo, tôi sẽ ghi chú lại chi tiết các bước thực thi và đặc biệt là cách tôi xử lý các **trục trặc kỹ thuật (troubleshooting)** trong từng phase.
