# Engineering Log 04: Real-time Vector AI Recommendation

## 1. Mục tiêu kỹ thuật
Ban đầu, tôi dự tính sử dụng OpenStack (hạ tầng IaaS) để lưu trữ dịch vụ AI. Tuy nhiên, sau khi đánh giá bài toán, việc nhồi nhét OpenStack vào máy cá nhân là một sự "quá khổ" (overkill) và đi ngược lại triết lý Microservices của dự án. 
Quyết định cuối cùng: Đóng gói (Containerize) hoàn toàn dịch vụ AI Recommendation thành một ứng dụng FastAPI siêu nhẹ, tích hợp Vector Database, và triển khai trực tiếp vào cụm Kubernetes dưới dạng một Pod hoạt động độc lập, sẵn sàng Scale khi cần.

## 2. Quá trình thực thi

### Thiết kế Dịch vụ AI (FastAPI + SentenceTransformers)
- Tôi sử dụng mô hình NLP `all-MiniLM-L6-v2`. Đây là mô hình sinh ra "Word Embeddings" (Vector 384 chiều) được tôi chọn lọc khắt khe vì nó đạt được sự cân bằng hoàn hảo giữa tốc độ cực nhanh (độ trễ dưới 25ms) và độ chính xác phân tích ngữ nghĩa (semantic similarity).
- Xây dựng 2 Endpoints chính trên FastAPI:
  - `/catalog`: Để Consumer nạp sản phẩm mới (tên thương hiệu, danh mục) vào hệ thống.
  - `/recommend`: Nhận thông tin sản phẩm khách đang xem và trả về top 5 sản phẩm tương đồng nhất dùng thuật toán Cosine Similarity.

### Tích hợp Milvus Lite
Thay vì dùng Milvus bản đầy đủ (yêu cầu hàng chục container đi kèm như MinIO, etcd), tôi dùng `pymilvus[model]` (Milvus Lite). Toàn bộ dữ liệu Vector được lưu trực tiếp vào ổ đĩa nội bộ (file `.db`), biến ứng dụng thành một cỗ máy Recommendation độc lập (Standalone) không phụ thuộc ngoại vi.

### Tối ưu hóa Docker Image
- Quá trình Build image chuẩn của PyTorch thường nặng tới 4-5GB, một con số không thể chấp nhận được trong kiến trúc Cloud-Native.
- Tôi đã can thiệp vào `Dockerfile`, chỉnh sửa để tải phiên bản `torch` dành riêng cho CPU (`--extra-index-url https://download.pytorch.org/whl/cpu`). 
- Kết quả: Kích thước Docker Image giảm mỡ chỉ còn ~1.4GB, triển khai cực kỳ nhanh chóng.

## 3. Trục trặc gặp phải & Cách giải quyết (Troubleshooting)

**Vấn đề 1: Tràn RAM (OOM - Out of Memory) khi Deploy lên Kubernetes**
*Nguyên nhân:* Mô hình AI khi load vào RAM sẽ tiêu tốn khoảng 500-600MB. Trong file Kubernetes Deployment (`ai-service.yaml`), nếu không cấu hình Resource Limits rõ ràng, K8s sẽ cho phép Pod tiêu thụ RAM không giới hạn, hoặc ngược lại, cấp quá ít dẫn đến Pod bị hệ điều hành Kill ngay lập tức (Lỗi `OOMKilled`).
*Cách giải quyết:* Tôi thiết lập ranh giới tài nguyên cứng rắn (Hard limits) trong file Deployment:
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```
Kết hợp với việc tạo các đầu dò (Probes: `livenessProbe` và `readinessProbe`) để K8s tự động theo dõi và khởi động lại Pod nếu AI engine bị treo.

## 4. Kết quả (Outcome)
Dịch vụ AI hoạt động trơn tru trong k3d cluster. Các truy vấn trả về kết quả sản phẩm tương đồng chỉ trong vài chục mili-giây, sẵn sàng đón nhận luồng dữ liệu khổng lồ từ Streaming Pipeline ở Phase tiếp theo.
