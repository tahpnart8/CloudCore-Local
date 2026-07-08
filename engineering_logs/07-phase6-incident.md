# Engineering Log 07: Kịch bản Sự cố & Mô phỏng Sức chịu đựng (Chaos Engineering)

## 1. Mục tiêu kỹ thuật
Để minh chứng rằng kiến trúc CloudCore không chỉ là một mô hình "chạy được" (Proof of Concept) mà còn thực sự "chống đạn" (Resilient), tôi đã tiến hành diễn tập 3 kịch bản sự cố kinh điển trong hệ thống phân tán (Chaos Engineering).
Mục đích là để đo lường các chỉ số cốt lõi của SRE:
- **MTTR (Mean Time To Recovery):** Thời gian trung bình để tự phục hồi.
- **Zero-downtime Maintenance:** Khả năng di dời ứng dụng không gián đoạn dịch vụ.
- **Elasticity:** Khả năng mở rộng ngang khi Traffic tăng đột biến.

## 2. Quá trình thực thi & Đánh giá (Postmortem)

### Kịch bản 1: Consumer Pod Crash (Đứt gãy luồng xử lý)
**Thao tác giả lập:** Tôi cố ý truy cập vào Container Consumer và tiêu diệt (kill) tiến trình chính để làm sập hệ thống.
**Phản ứng của hệ thống:**
1. Kubernetes (Kubelet) lập tức phát hiện Pod mất trạng thái `Ready` thông qua Liveness Probe.
2. ReplicaSet tự động khởi tạo Pod thay thế.
3. Pod mới ngay lập tức kết nối lại vào Redpanda Broker và tiếp tục đọc bản ghi dữ liệu (messages) nhờ cơ chế Kafka Offset Commit, đảm bảo **không có bất kỳ event nào bị rớt hoặc xử lý trùng lặp (Exactly-once / At-least-once processing)**.
**Kết quả:** Thời gian tự phục hồi (MTTR) đo được trên Grafana là **~8 giây**. Toàn bộ dữ liệu doanh thu vẫn nhất quán.

### Kịch bản 2: E-Commerce Traffic Surge (Bão truy cập tăng gấp 5 lần)
**Thao tác giả lập:** Tôi tăng tốc độ bơm dữ liệu của Producer từ `120x` lên `600x` để mô phỏng chiến dịch Flash Sale, gây nghẽn cổ chai (Bottleneck) tại Consumer.
**Phản ứng của hệ thống:**
1. Quan sát trên Dashboard, Consumer Lag bắt đầu tăng vọt do không xử lý kịp hàng ngàn events mỗi giây.
2. Tôi tiến hành mở rộng ngang (Horizontal Scaling) bằng lệnh `kubectl scale deployment --replicas=3`.
3. 3 Pods Consumer lập tức phân chia nhau đọc các Phân vùng dữ liệu (Kafka Partitions) dựa trên cơ chế Consumer Group.
**Kết quả:** Tốc độ tiêu thụ dữ liệu nhân lên gấp 3, Consumer Lag giảm nhanh chóng về 0. Hệ thống chứng minh khả năng "đỡ đạn" trước lưu lượng siêu lớn.

### Kịch bản 3: Node Drain (Bảo trì Server vật lý)
**Thao tác giả lập:** Mô phỏng tình huống Agent Node cần cập nhật Kernel hoặc thay RAM. Tôi sử dụng lệnh `kubectl drain` để ra lệnh sơ tán toàn bộ dịch vụ khỏi Node này.
**Phản ứng của hệ thống:**
1. Kubernetes đưa Agent Node vào trạng thái `SchedulingDisabled` (Cấm nhận thêm việc).
2. Các dịch vụ đang chạy trên Agent Node bị K8s ra lệnh `evict` (trục xuất) một cách duyên dáng (Graceful Shutdown).
3. Ngay lập tức, K8s tái tạo lại các dịch vụ này trên Server Node (nơi đang rảnh rỗi hơn) trong lúc Node cũ bảo trì.
**Kết quả:** Hệ thống di dời (Migration) các thành phần lõi mà không gây ra giây phút Downtime nào.

## 3. Tổng kết Dự án
Dự án **CloudCore** kết thúc thành công mỹ mãn. Việc ứng dụng nghiêm ngặt các nguyên tắc SRE và Cloud-Native đã chứng minh được sức mạnh của một kiến trúc phân tán hiện đại. Từ một tập dữ liệu E-commerce dạng tĩnh, tôi đã xây dựng nên một cỗ máy luân chuyển sự kiện, phân tích ngữ nghĩa AI, và tự động phục hồi sự cố một cách hoàn hảo.
