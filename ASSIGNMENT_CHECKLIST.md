# Milestone 4 Test_1 作业检查清单

## ✅ 已完成的部分

### 1. Code and Configuration
- ✅ 所有源代码已组织在仓库中
  - `src/api_service/` - API 服务
  - `aimino_frontend/` - 前端和核心模块
  - `tests/` - 测试文件（unit, integration, system）
  
- ✅ CI/CD 配置文件
  - `.github/workflows/ci.yml` - GitHub Actions CI pipeline
  - `docker-compose.test.yml` - Docker Compose 测试配置
  - `pytest.ini` - Pytest 配置
  - `src/api_service/pyproject.toml` - 项目配置和测试依赖

- ✅ README 文档
  - `README.md` - 项目说明和设置指南
  - `TESTING.md` - 详细的测试文档

## 📋 需要完成的步骤

### 步骤 1: 本地测试（确保一切正常）

```bash
cd "/Users/ytian/Documents/School Courses/Biostatistics_2025Fall/AC 215/Project/Milestone 4 Test_1/AC215_AIMinO"

# 方式 1: 使用 Docker Compose（推荐）
docker-compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from test_runner

# 方式 2: 本地运行（需要安装依赖）
pip install pytest pytest-cov pytest-mock requests fastapi[all]
export PYTHONPATH=$PWD/src:$PWD/aimino_frontend/aimino_core
pytest tests/ -v --cov=src/api_service --cov=aimino_frontend/aimino_core --cov-report=html
```

**检查点：**
- ✅ 所有测试通过
- ✅ 覆盖率 >= 50%
- ✅ 没有错误或警告

### 步骤 2: 提交代码到 GitHub

```bash
# 检查 Git 状态
git status

# 添加所有新文件
git add .github/workflows/ci.yml
git add docker-compose.test.yml
git add pytest.ini
git add tests/
git add TESTING.md
git add README.md
git add src/api_service/pyproject.toml

# 提交
git commit -m "Add CI/CD pipeline and comprehensive test suite"

# 推送到 GitHub
git push origin main  # 或你的分支名
```

### 步骤 3: 在 GitHub 上运行 CI

1. 打开 GitHub 仓库
2. 点击 **Actions** 标签
3. 等待 CI pipeline 运行完成
4. 检查以下内容：
   - ✅ **Build and Test with Docker Compose** - 应该通过（绿色 ✓）
   - ✅ **Lint and Format Check** - 应该通过或警告
   - ✅ **Test Summary** - 应该显示所有测试通过

### 步骤 4: 获取 CI 截图

需要截图的页面：

1. **CI Pipeline 运行页面**
   - 显示所有 jobs 的状态
   - 显示运行时间
   - 路径：`Actions` → 点击最新的 workflow run

2. **Build and Test Job 详情**
   - 显示测试运行结果
   - 显示覆盖率报告
   - 点击 `Build and Test with Docker Compose` job

3. **Coverage Report**
   - 下载 coverage artifact
   - 打开 `htmlcov/index.html`
   - 截图显示覆盖率 >= 50%

### 步骤 5: 验证覆盖率

```bash
# 在 CI 中检查覆盖率
# 或者在本地运行：
pytest tests/ --cov=src/api_service --cov=aimino_frontend/aimino_core --cov-report=term --cov-fail-under=50
```

**要求：**
- ✅ 覆盖率 >= 50%
- ✅ 覆盖率报告已生成（HTML 和 XML）

## 📸 需要提交的截图

1. **CI Pipeline 运行成功截图**
   - 显示所有 jobs 通过
   - 显示运行时间

2. **测试结果截图**
   - 显示所有测试通过
   - 显示测试数量

3. **覆盖率报告截图**
   - 显示覆盖率 >= 50%
   - 显示覆盖率详情

4. **Linting 结果截图**（如果有）
   - 显示 linting 通过或警告

## 🔍 故障排除

### 如果 CI 失败：

1. **检查日志**
   ```bash
   # 查看 CI 日志
   # 在 GitHub Actions 页面点击失败的 job
   ```

2. **本地复现问题**
   ```bash
   docker-compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from test_runner
   ```

3. **常见问题**
   - 测试失败 → 检查测试代码
   - 覆盖率不足 → 添加更多测试
   - Docker 构建失败 → 检查 Dockerfile
   - 依赖问题 → 检查 pyproject.toml

### 如果覆盖率不足：

1. **添加更多测试**
   ```bash
   # 查看哪些代码没有被覆盖
   pytest --cov=src/api_service --cov=aimino_frontend/aimino_core --cov-report=term-missing
   ```

2. **针对未覆盖的代码编写测试**

## ✅ 最终检查清单

在提交作业前，确保：

- [ ] 所有源代码已提交到 GitHub
- [ ] CI 配置文件已提交（`.github/workflows/ci.yml`）
- [ ] README 已更新，包含设置和运行说明
- [ ] CI pipeline 运行成功
- [ ] 所有测试通过
- [ ] 代码覆盖率 >= 50%
- [ ] 已获取所有需要的截图
- [ ] 截图清晰显示要求的内容

## 📝 提交作业

提交时包含：
1. GitHub 仓库链接
2. CI 运行截图（3-4 张）
3. 简要说明：
   - CI 配置位置
   - 如何运行测试
   - 覆盖率结果

