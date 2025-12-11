# CI/CD Pipeline 说明

本目录包含GitHub Actions工作流配置，用于自动化测试、构建和部署。

## 工作流文件

- `ci-cd.yml`: 主要的CI/CD pipeline，包含测试、构建和部署步骤

## Pipeline 流程

### 1. 测试阶段 (Test Job)

- 在Python 3.10, 3.11, 3.12上运行单元测试
- 运行集成测试
- 检查代码覆盖率（要求≥60%）
- 生成覆盖率报告

### 2. 构建阶段 (Build Job)

- 构建Docker镜像
- 推送到GitHub Container Registry (ghcr.io)
- 使用Docker layer缓存加速构建

### 3. 系统测试阶段 (System Test Job)

- 启动API服务容器
- 运行端到端系统测试
- 验证服务功能

### 4. 部署阶段 (Deploy Job)

- **仅在合并到main分支时触发**
- 部署到Kubernetes集群
- 验证部署状态

### 5. 覆盖率报告 (Coverage Report Job)

- 生成详细的覆盖率文档
- 记录未测试的模块和函数
- 更新`COVERAGE_REPORT.md`

## 触发条件

- **Push事件**: 推送到`main`、`master`或`develop`分支
- **Pull Request**: 创建或更新PR到`main`、`master`或`develop`分支
- **部署**: 仅在合并到`main`分支时自动触发

## 配置要求

### GitHub Secrets

需要在GitHub仓库的Settings > Secrets中配置以下secrets：

1. **KUBECONFIG** (可选，仅用于Kubernetes部署)
   - 包含kubectl配置文件内容
   - 用于连接到Kubernetes集群

### 环境变量

Pipeline使用以下环境变量（可在workflow文件中修改）：

- `PYTHON_VERSION`: Python版本（默认3.12）
- `DOCKER_IMAGE_NAME`: Docker镜像名称（默认aimino-api）
- `DOCKER_REGISTRY`: Docker镜像仓库（默认ghcr.io）

## 覆盖率要求

根据作业要求，项目必须达到**至少60%的代码覆盖率**。

- 如果覆盖率低于60%，测试阶段会失败
- 覆盖率报告会自动生成并上传为artifact
- 详细的覆盖率文档保存在`COVERAGE_REPORT.md`

## 查看结果

1. 在GitHub仓库的**Actions**标签页查看pipeline运行状态
2. 下载artifact查看：
   - 覆盖率报告（HTML格式）
   - 测试结果（JUnit XML格式）
   - 覆盖率文档

## 故障排查

### 测试失败

- 检查测试日志中的错误信息
- 确保所有依赖已正确安装
- 验证测试环境配置

### 构建失败

- 检查Dockerfile是否正确
- 验证依赖项是否可用
- 检查Docker registry权限

### 部署失败

- 确认KUBECONFIG secret已配置
- 检查Kubernetes集群连接
- 验证RBAC权限
- 确认k8s/deployment.yaml文件存在

### 覆盖率不足

- 查看`COVERAGE_REPORT.md`了解未测试的模块
- 添加更多单元测试和集成测试
- 确保测试标记正确（`@pytest.mark.unit`、`@pytest.mark.integration`）

## 本地测试

在提交代码前，可以在本地运行相同的测试：

```bash
# 运行所有测试
pytest

# 检查覆盖率
pytest --cov=src/api_service --cov=aimino_frontend --cov-fail-under=60

# 运行特定类型的测试
pytest -m unit
pytest -m integration
pytest -m system
```

## 自定义配置

如果需要修改pipeline行为，编辑`.github/workflows/ci-cd.yml`文件：

- 修改Python版本矩阵
- 添加额外的测试步骤
- 自定义部署流程
- 调整覆盖率阈值

## 注意事项

1. **部署权限**: 确保GitHub Actions有权限推送到Docker registry和部署到Kubernetes
2. **Secret安全**: 不要在代码中硬编码敏感信息，使用GitHub Secrets
3. **资源限制**: 注意CI runner的资源限制，避免超时
4. **缓存策略**: Pipeline使用缓存加速构建，但可能需要定期清理

