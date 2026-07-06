# ☁️ CloudCore Local — Cloud-Native E-Commerce & AI Streaming Engine

[![Kubernetes](https://img.shields.io/badge/Kubernetes-k3d%2Fk3s-blue.svg)](https://k3s.io/)
[![Terraform](https://img.shields.io/badge/IaC-Terraform-purple.svg)](https://www.terraform.io/)
[![Ansible](https://img.shields.io/badge/Config-Ansible-red.svg)](https://www.ansible.com/)
[![Redpanda](https://img.shields.io/badge/Streaming-Redpanda-ff69b4.svg)](https://redpanda.com/)
[![AI Inference](https://img.shields.io/badge/AI-FastAPI%20%2B%20SentenceTransformers-green.svg)](https://fastapi.tiangolo.com/)
[![Observability](https://img.shields.io/badge/Monitoring-Prometheus%20%2B%20Grafana-orange.svg)](https://prometheus.io/)

---

## 📌 Tổng Quan Dự Án (Project Overview)

**CloudCore Local** là một dự án thí nghiệm hạ tầng Cloud-Native thiên hướng Enterprise được xây dựng và triển khai hoàn toàn trên môi trường local (Docker Desktop + WSL2 Ubuntu). 

Dự án mô phỏng một **Hệ thống E-commerce Real-Time Streaming kết hợp AI Recommendation**, tự động xử lý hàng triệu sự kiện mua sắm, tính toán doanh thu theo cửa sổ thời gian (Tumbling Window), lọc dữ liệu rác (Data Cleansing) và đưa ra gợi ý sản phẩm cá nhân hóa bằng mô hình học máy (Vector Search) trong thời gian thực.

---

## 🏗️ Kiến Trúc Hệ Thống (System Architecture)


<img width="1899" height="940" alt="CloudCore Local drawio" src="https://github.com/user-attachments/assets/16c07bcb-b362-46ca-a1da-1cde906aa265" />

---
## Dashboard Demo
<img width="1899" height="940" alt="Screenshot 2026-07-06 035013" src="https://github.com/user-attachments/assets/4c5ae662-ffbf-4449-8b99-905154c0053e" />
---

## 🚀 Các Bước Triển Khai Chi Tiết (Implementation Roadmap)

### 🔹 Phase 1: Infrastructure as Code (IaC) với Terraform & k3d
- Khởi tạo cụm Kubernetes gồm 2 Nodes (**1 Server Node + 1 Agent Node**) tự động bằng **Terraform**.
- Đóng gói toàn bộ cấu hình cụm vào các file HCL (`main.tf`, `variables.tf`, `outputs.tf`).
- Cho phép phá hủy (destroy) và dựng lại toàn bộ hạ tầng chỉ trong **~3 phút**.

### 🔹 Phase 2: Configuration Management & OS Hardening với Ansible
- Xây dựng Ansible Playbook tự động bảo mật cho hệ thống Linux.
- **UFW Firewall:** Thiết lập tường lửa chỉ mở các cổng thiết yếu (22, 80, 443, 6443, 3000, 9090).
- **Fail2ban:** Tự động phát hiện và chặn các đợt tấn công brute-force SSH.
- **Chrony:** Đồng bộ thời gian thực chuẩn xác giữa các Nodes trong cụm.

### 🔹 Phase 3: Real-Time Vector AI Recommendation Service
- Triển khai dịch vụ AI bằng **FastAPI** và mô hình nhúng ngôn ngữ `SentenceTransformers (all-MiniLM-L6-v2)`.
- Lưu trữ chỉ mục ngữ nghĩa (embedding vector) của sản phẩm trong in-memory store, tìm kiếm bằng Cosine Similarity thủ công qua NumPy. (Ghi chú: phiên bản hiện tại chưa tích hợp vector database chuyên dụng như Milvus/Pinecone — đây là hướng nâng cấp tiếp theo khi cần scale catalog lớn hơn.)
- **Feature Engineering:** Tự động hợp nhất các thông tin rời rạc (`brand` + `category_code`) thành chuỗi văn bản nhận diện tính chất sản phẩm.
- Cung cấp 2 API chính:
  - `/catalog`: Nạp thông tin vector sản phẩm vào cơ sở dữ liệu.
  - `/recommend`: Tìm kiếm 3 sản phẩm có độ tương đồng ngữ nghĩa cao nhất (Cosine Similarity) cho người dùng trong thời gian thực.

### 🔹 Phase 4: Real-Time Streaming Pipeline & Stream Data Cleansing
- Triển khai **Redpanda Broker** (môi trường Kafka siêu tốc độ, hiệu năng cao).
- **Producer Pod:** Đọc bộ dữ liệu 4,1 triệu dòng từ Kaggle và phát lại vào Redpanda với tốc độ nén thời gian **120x - 600x**.
- **Consumer Pod & Tumbling Window:**
  - Thu thập event stream và tính toán chỉ số kinh doanh theo cửa sổ 30 giây (`Tumbling Window 30s`): Tổng số views, carts, purchases, tổng doanh thu ($) và tỷ lệ chuyển đổi (Conversion Rate).
  - Expose toàn bộ metrics theo chuẩn Prometheus ở cổng `:8001`.
- **Stream Data Cleansing (Xử lý dữ liệu rác):**
  - Tự động lọc bỏ các sự kiện bị khuyết cả 2 trường `brand` và `category_code` trước khi gửi sang AI, giúp AI luôn trả về những gợi ý thông minh và chính xác.
  - Vẫn giữ nguyên 100% dữ liệu để tính toán doanh thu kinh doanh cho Prometheus.

### 🔹 Phase 5: Full-Stack Observability (Prometheus + Grafana + Alertmanager)
- Cài đặt bộ công cụ giám sát chuẩn Cloud-Native `kube-prometheus-stack` qua **Helm**.
- Cấu hình `ServiceMonitor` để Prometheus tự động thu thập (scrape) metrics từ Consumer mỗi 15 giây.
- Thiết lập **Alert Rules** tự động phát hiện sự cố (VD: `PipelineStopped` khi không có event trong 3 phút).
- Xây dựng **Grafana Dashboard** trực quan hiển thị dòng tiền, lưu lượng traffic và sức khỏe hạ tầng thời gian thực.

### 🔹 Phase 6: Incident Simulation & Postmortem Documentation
Mô phỏng 3 kịch bản sự cố Production thực tế để kiểm tra tính bền bỉ và khả năng tự phục hồi (Self-Healing) của hệ thống:
1. **Kịch bản 1: Consumer Pod Crash (Sập ứng dụng)**
   - Mô phỏng ngắt đột ngột Pod Consumer.
   - **Kết quả:** Kubernetes tự động khởi tạo Pod thay thế, khôi phục xử lý từ Kafka offset đã commit. **MTTR = 8 giây**, không mất mát dữ liệu.
2. **Kịch bản 2: Traffic Surge (Tăng tải đột ngột 5x)**
   - Tăng tốc độ sinh sự kiện lên 500% (`SPEED_FACTOR=600`).
   - **Kết quả:** Thực hiện scale ngang Consumer từ 1 lên 3 Replicas. Kafka Consumer Group tự động rebalance partition, chia đều tải và giải tỏa nghẽn dữ liệu.
3. **Kịch bản 3: Node Drain (Bảo trì Máy chủ)**
   - Thực hiện `cordon` và `drain` trên node `agent-0`.
   - **Kết quả:** Toàn bộ các Pods trên agent-0 được di dời an toàn sang `server-0` với **Downtime = 0**.

---

## Thông Số Kỹ Thuật Đạt Được (Key Metrics & Benchmarks)

| Chỉ số (Metric) | Giá trị thực tế (Measured Value) |
|---|---|
| **Thời gian tạo mới toàn bộ Cụm (IaC)** | **~3 phút** (Terraform + k3d) |
| **Số lượng Node Kubernetes** | **2 Nodes** (1 Server + 1 Agent) |
| **Tốc độ xử lý Streaming Pipeline** | **1,500+ events/giây** (Replay 120x - 600x) |
| **Thời gian khôi phục sự cố sập Pod (MTTR)** | **~8 giây** (Zero Data Loss) |
| **Độ trễ AI Suggestion (Inference Latency)** | **< 25 ms / request** |
| **Bảo trì Node không gián đoạn (Downtime)** | **0 giây** (Rolling migration) |

---

## 📁 Cấu Trúc Thư Mục Dự Án (Project Structure)

```
CloudCore-Local/
├── terraform/          # Mã nguồn IaC tạo cụm k3d/k3s
├── ansible/            # Playbooks bảo mật & cấu hình OS Hardening
├── streaming/          # Mã nguồn Python Producer & Consumer
│   ├── producer/       # Script replay dữ liệu 42M dòng
│   └── consumer/       # Script tính Tumbling Window & Data Cleansing
├── ai/                 # Dịch vụ AI Recommendation (FastAPI + SentenceTransformers, in-memory vector store)
├── k8s/                # Kubernetes Manifests (Deployments, Services, ServiceMonitors)
│   ├── streaming/      # Redpanda, Producer, Consumer YAMLs
│   └── monitoring/     # PrometheusRules, ServiceMonitors YAMLs
├── runbooks/           # Hồ sơ Postmortem 3 kịch bản sự cố Production
│   ├── incident-01-consumer-crash.md
│   ├── incident-02-traffic-surge.md
│   └── incident-03-node-drain.md
└── guides/             # Bộ tài liệu hướng dẫn từng bước 6 Phases (Step-by-step)
```

