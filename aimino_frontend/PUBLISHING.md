# 发布指南 (Publishing Guide)

本指南说明如何将 `aimino` 包发布到 PyPI。

## 准备工作

### 1. 更新版本号

在 `pyproject.toml` 中更新版本号：

```toml
version = "0.1.0"  # 更新为新的版本号，如 "0.1.1" 或 "0.2.0"
```

遵循 [语义化版本](https://semver.org/)：
- **MAJOR**: 不兼容的 API 变更
- **MINOR**: 向后兼容的功能添加
- **PATCH**: 向后兼容的 bug 修复

### 2. 更新项目 URL（可选）

如果项目有 GitHub 仓库，在 `pyproject.toml` 中更新 `[project.urls]` 部分：

```toml
[project.urls]
Homepage = "https://github.com/your-org/aimino"
Documentation = "https://github.com/your-org/aimino#readme"
Repository = "https://github.com/your-org/aimino"
Issues = "https://github.com/your-org/aimino/issues"
```

### 3. 检查文件

确保以下文件存在且内容正确：
- ✅ `pyproject.toml` - 包配置
- ✅ `README.md` - 项目说明
- ✅ `LICENSE` - MIT 许可证
- ✅ `MANIFEST.in` - 包含的文件清单
- ✅ `.gitignore` - Git 忽略规则

## 构建分发包

### 安装构建工具

```bash
pip install build twine
```

### 构建分发包

在 `aimino_frontend` 目录下运行：

```bash
python -m build
```

这将生成：
- `dist/aimino-0.1.0-py3-none-any.whl` - 轮子文件（wheel）
- `dist/aimino-0.1.0.tar.gz` - 源码分发包

### 检查分发包

在发布前检查分发包内容：

```bash
# 检查轮子文件
python -m zipfile -l dist/aimino-*.whl

# 检查源码包
tar -tzf dist/aimino-*.tar.gz | head -20
```

### 验证分发包

使用 `twine` 检查分发包：

```bash
twine check dist/*
```

## 发布到 PyPI

### 1. 测试发布到 TestPyPI（推荐）

首先发布到 TestPyPI 进行测试：

```bash
# 上传到 TestPyPI
twine upload --repository testpypi dist/*

# 测试安装
pip install --index-url https://test.pypi.org/simple/ aimino
```

### 2. 发布到正式 PyPI

确认测试无误后，发布到正式 PyPI：

```bash
twine upload dist/*
```

**注意**：需要 PyPI 账号和 API token。可以在 [PyPI](https://pypi.org/manage/account/) 创建账号并生成 token。

### 3. 使用 API Token（推荐）

创建 `~/.pypirc` 文件：

```ini
[pypi]
username = __token__
password = pypi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

然后直接运行：

```bash
twine upload dist/*
```

## 验证发布

发布后，可以通过以下方式验证：

```bash
# 等待几分钟让 PyPI 索引更新
pip install aimino

# 验证安装
python -c "import aimino_frontend; print(aimino_frontend.__version__)"
```

## 常见问题

### 包名已被占用

如果 `aimino` 已被占用，可以：
1. 使用其他名称（如 `aimino-napari`）
2. 联系 PyPI 管理员

### 版本号冲突

如果版本号已存在，需要更新版本号后重新发布。

### 依赖问题

确保所有依赖都在 PyPI 上可用。如果使用私有依赖，需要：
1. 将私有依赖也发布到 PyPI
2. 或使用 `--find-links` 指定额外的索引

## 更新已发布的包

1. 更新 `pyproject.toml` 中的版本号
2. 重新构建：`python -m build`
3. 重新上传：`twine upload dist/*`

**重要**：PyPI 不允许覆盖已发布的版本，只能发布新版本。

