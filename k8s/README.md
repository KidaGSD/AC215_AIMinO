# Kubernetes 部署配置

此目录包含用于将AIMinO API服务部署到Kubernetes集群的配置文件。

## 文件说明

- `deployment.yaml`: Kubernetes Deployment、Service和PVC配置

## 使用方法

### 前置要求

1. 配置kubectl连接到你的Kubernetes集群
2. 创建必要的Secrets（包含GEMINI_API_KEY等敏感信息）
3. 确保有足够的存储资源

### 创建Secrets

```bash
kubectl create secret generic aimino-secrets \
  --from-literal=gemini-api-key=YOUR_API_KEY
```

### 部署应用

```bash
# 应用配置
kubectl apply -f k8s/deployment.yaml

# 检查部署状态
kubectl get deployments
kubectl get pods -l app=aimino-api
kubectl get services -l app=aimino-api

# 查看日志
kubectl logs -f deployment/aimino-api
```

### 更新镜像

当GitHub Actions构建新镜像后，可以通过以下方式更新：

```bash
# 方法1: 使用kubectl set image
kubectl set image deployment/aimino-api \
  aimino-api=ghcr.io/YOUR_USERNAME/YOUR_REPO/aimino-api:NEW_TAG

# 方法2: 触发滚动更新
kubectl rollout restart deployment/aimino-api

# 查看更新状态
kubectl rollout status deployment/aimino-api
```

### 在GitHub Actions中使用

GitHub Actions workflow中的deploy job会自动执行部署。确保：

1. 在GitHub仓库的Secrets中配置`KUBECONFIG`
2. 更新`.github/workflows/ci-cd.yml`中的部署步骤，取消注释并配置正确的镜像路径

## 配置说明

### 资源限制

默认配置：
- 请求: 512Mi内存, 250m CPU
- 限制: 2Gi内存, 1000m CPU

根据实际需求调整`deployment.yaml`中的resources部分。

### 存储

默认配置10Gi的持久化存储。如果需要更多存储，修改PVC的`storage`字段。

### 环境变量

在`deployment.yaml`中配置的环境变量：
- `GEMINI_API_KEY`: 从Secret中读取
- `AIMINO_DATA_ROOT`: 数据存储路径
- `AIMINO_SKIP_STARTUP`: 是否跳过启动检查

## 故障排查

```bash
# 查看Pod状态
kubectl describe pod <pod-name>

# 查看事件
kubectl get events --sort-by='.lastTimestamp'

# 进入Pod调试
kubectl exec -it <pod-name> -- /bin/bash

# 查看服务端点
kubectl get endpoints aimino-api-service
```

