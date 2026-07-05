# Incident 03: Node Drain — Bảo Trì Worker Node

**Date:** 2026-07-05
**Duration:** ~2 minutes
**Severity:** P3 (Bảo trì có kế hoạch)

## Summary
Tiến hành bảo trì định kỳ cho Worker Node `k3d-cloudcore-agent-0`. Thực hiện `cordon` để chặn pod mới và `drain` để di dời an toàn toàn bộ các Pods đang chạy sang Node còn lại (`k3d-cloudcore-server-0`). Sau khi hoàn tất, khôi phục Node (`uncordon`) trở lại trạng thái khả dụng.

## Timeline
- 22:13:33 — Thực hiện lệnh `kubectl cordon k3d-cloudcore-agent-0` (vô hiệu hóa lập lịch trên agent-0)
- 22:13:34 — Đánh dấu Node `Ready,SchedulingDisabled`
- 22:13:35 — Thực hiện `kubectl drain k3d-cloudcore-agent-0` để di dời các Pods
- 22:13:50 — Tất cả Pods trên agent-0 được terminate và tự động tạo lại trên `k3d-cloudcore-server-0`
- 22:14:17 — Bảo trì hoàn tất, thực hiện `kubectl uncordon k3d-cloudcore-agent-0` đưa Node về trạng thái `Ready`

## Root Cause
- **Mô phỏng:** Bảo trì định kỳ hạ tầng (Nâng cấp Kernel OS, cập nhật phiên bản K3s/Docker).
- **Thực tế Production:** Thay thế phần cứng lỗi, nâng cấp cấu hình máy chủ vật lý.

## Impact
- Không có thời gian chết (Downtime = 0) do các Pods được điều phối di dời lần lượt.
- Toàn bộ các dịch vụ (Grafana, Consumer, Producer, Redpanda) đều tiếp tục hoạt động bình thường trên Node server-0.

## Remediation
- Sử dụng đúng quy trình bảo trì K8s tiêu chuẩn: `cordon` -> `drain` -> `uncordon`.
- Kubernetes Scheduler tự động tái phân bổ Pods sang Node khỏe mạnh.

## Action Items
- [x] Thiết lập PodDisruptionBudgets (PDB) cho các dịch vụ cốt lõi để tránh bị eviction đồng thời
- [x] Xây dựng quy trình tự động hóa Rolling Drain khi nâng cấp Cluster
- [x] Đánh giá tải năng lực của Server Node khi 1 Agent Node bị ngắt kết nối

## Lessons Learned
1. Quy trình `cordon` -> `drain` -> `uncordon` của Kubernetes xử lý di dời Pods vô cùng mượt mà.
2. Việc phân bổ tài nguyên hợp lý giữa các Nodes giúp cụm máy chủ chịu tải tốt ngay cả khi khuyết 1 Worker Node.
