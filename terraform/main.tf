# ============================================================
# CloudCore Local — Terraform Configuration
# Mục đích: Tạo Docker network + k3d Kubernetes cluster
# ============================================================

# --- KHAI BÁO PROVIDER ---
# Terraform cần biết nó sẽ "nói chuyện" với nền tảng nào.
# Ở đây ta dùng Docker provider (kreuzwerker/docker) để
# tạo Docker network. k3d cluster sẽ dùng null_resource
# vì k3d chưa có native Terraform provider.
terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"       # Dùng version 3.x (ổn định)
    }
  }
}

# Provider Docker — kết nối với Docker daemon local
# (Docker Desktop đã share daemon qua WSL2 integration)
provider "docker" {}

# --- RESOURCE 1: Docker Network ---
# Tạo một mạng riêng cho cluster, giống như tạo VLAN 
# trong mạng doanh nghiệp. Các container trong cùng
# network có thể nói chuyện với nhau bằng tên.
resource "docker_network" "cloudcore" {
  name   = "cloudcore-net"
  driver = "bridge"           # Bridge = mạng ảo local
  
  ipam_config {
    subnet  = "172.20.0.0/16" # Dải IP cho network (65,534 địa chỉ)
    gateway = "172.20.0.1"    # Gateway (cổng ra) của network
  }
}

# --- RESOURCE 2: k3d Cluster ---
# Dùng null_resource + local-exec vì k3d không có 
# Terraform provider chính thức. local-exec cho phép
# chạy lệnh shell trực tiếp.
resource "null_resource" "k3d_cluster" {
  # Đảm bảo network được tạo TRƯỚC khi tạo cluster
  depends_on = [docker_network.cloudcore]

  # PROVISIONER TẠO — chạy khi terraform apply
  provisioner "local-exec" {
    command = <<-EOT
      k3d cluster create cloudcore \
        --servers 1 \
        --agents 1 \
        --network cloudcore-net \
        --api-port 6443 \
        --port "3000:3000@loadbalancer" \
        --port "9090:9090@loadbalancer"
    EOT
  }

  # PROVISIONER HỦY — chạy khi terraform destroy
  provisioner "local-exec" {
    when    = destroy
    command = "k3d cluster delete cloudcore"
  }
}

# --- OUTPUT ---
# Hiển thị thông tin sau khi tạo xong
output "cluster_info" {
  value = "Cluster 'cloudcore' đã tạo! Chạy: kubectl get nodes"
}
