# PyPI 发布完整指南

本指南将详细说明如何将 `aimino` 包打包并发布到 PyPI，让用户可以通过 `pip install aimino` 安装。

---

## 📋 目录

1. [准备工作](#准备工作)
2. [配置检查](#配置检查)
3. [构建分发包](#构建分发包)
4. [测试发布](#测试发布)
5. [正式发布](#正式发布)
6. [验证发布](#验证发布)
7. [常见问题](#常见问题)
8. [更新已发布的包](#更新已发布的包)

---

## 一、准备工作

### 1.1 注册 PyPI 账号

1. 访问 [PyPI 官网](https://pypi.org/)
2. 点击右上角 "Register" 注册账号
3. 验证邮箱并完成注册

### 1.2 创建 API Token（推荐）

**为什么使用 API Token？**
- 更安全：不需要使用密码
- 可以撤销：如果泄露可以立即撤销
- 可以设置权限：只允许上传特定项目

**创建步骤：**

1. 登录 PyPI 后，访问 [Account settings](https://pypi.org/manage/account/)
2. 滚动到 "API tokens" 部分
3. 点击 "Add API token"
4. 填写：
   - **Token name**: 例如 `aimino-upload-token`
   - **Scope**: 选择 "Entire account" 或 "Project: aimino"
5. 点击 "Add token"
6. **重要**：立即复制 token（格式：`pypi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`），因为之后无法再查看

### 1.3 安装必要的工具

在终端中运行：

```bash
# 安装构建工具和上传工具
pip install build twine

# 验证安装
python -m build --version
twine --version
```

---

## 二、配置检查

### 2.1 检查 pyproject.toml

确保 `pyproject.toml` 中的关键配置正确：

```toml
[project]
name = "aimino"  # 包名，必须是唯一的
version = "0.1.0"  # 版本号，遵循语义化版本
description = "AIMinO Napari frontend application with command execution and agent client"
requires-python = ">=3.10"
readme = "README.md"
license = {file = "LICENSE"}
authors = [
    {name = "AIMinO Team: Yingxiao (TK) Shi, Kida Huang, Yinuo Cheng, Yuan Tian"}
]
```

**重要检查项：**
- ✅ 包名 `aimino` 是否可用（可能已被占用，需要检查）
- ✅ 版本号是否正确
- ✅ 所有依赖项是否都在 PyPI 上可用
- ✅ 作者信息是否正确

### 2.2 检查必需文件

确保以下文件存在且内容正确：

```bash
cd aimino_frontend

# 检查文件是否存在
ls -la README.md LICENSE MANIFEST.in pyproject.toml
```

**必需文件清单：**
- ✅ `pyproject.toml` - 包配置文件
- ✅ `README.md` - 项目说明文档
- ✅ `LICENSE` - 许可证文件（MIT）
- ✅ `MANIFEST.in` - 包含的文件清单
- ✅ `src/aimino_frontend/` - 源代码目录

### 2.3 检查包名是否可用

在发布前，检查包名是否已被占用：

1. 访问 https://pypi.org/project/aimino/
2. 如果显示 "404 - This project could not be found"，说明包名可用
3. 如果包名已被占用，需要：
   - 修改 `pyproject.toml` 中的 `name` 字段（如改为 `aimino-napari`）
   - 或者联系 PyPI 管理员

### 2.4 更新版本号（如需要）

遵循 [语义化版本](https://semver.org/lang/zh-CN/)：

- **MAJOR** (主版本号): 当你做了不兼容的 API 修改
- **MINOR** (次版本号): 当你做了向下兼容的功能性新增
- **PATCH** (修订号): 当你做了向下兼容的问题修正

例如：
- `0.1.0` → `0.1.1` (修复 bug)
- `0.1.0` → `0.2.0` (新增功能)
- `0.1.0` → `1.0.0` (重大变更)

在 `pyproject.toml` 中更新：

```toml
version = "0.1.0"  # 改为新版本号
```

---

## 三、构建分发包

### 3.1 清理旧的构建文件

```bash
cd aimino_frontend

# 删除旧的构建文件
rm -rf dist/ build/ *.egg-info/
```

### 3.2 构建分发包

```bash
# 确保在 aimino_frontend 目录下
python -m build
```

**输出：**
```
* Creating venv isolated environment...
* Installing packages in isolated environment...
* Getting dependencies to build wheel...
* Installing packages in isolated environment...
* Building wheel...
* Building sdist...
Successfully built aimino-0.1.0-py3-none-any.whl and aimino-0.1.0.tar.gz
```

**生成的文件：**
- `dist/aimino-0.1.0-py3-none-any.whl` - 轮子文件（wheel，推荐）
- `dist/aimino-0.1.0.tar.gz` - 源码分发包（sdist）

### 3.3 检查分发包内容

**检查 wheel 文件：**

```bash
# 列出 wheel 文件内容
python -m zipfile -l dist/aimino-*.whl | head -30
```

应该看到：
- `aimino_frontend/` 目录及其所有 Python 文件
- `README.md`
- `LICENSE`
- `pyproject.toml`

**检查源码包：**

```bash
# 列出 tar.gz 文件内容
tar -tzf dist/aimino-*.tar.gz | head -30
```

### 3.4 验证分发包

使用 `twine` 检查分发包：

```bash
twine check dist/*
```

**期望输出：**
```
Checking dist/aimino-0.1.0-py3-none-any.whl: PASSED
Checking dist/aimino-0.1.0.tar.gz: PASSED
```

如果出现错误，根据提示修复后重新构建。

---

## 四、测试发布

### 4.1 注册 TestPyPI 账号

1. 访问 [TestPyPI](https://test.pypi.org/)
2. 注册账号（可以与 PyPI 使用相同的用户名）
3. 创建 API Token（步骤与 PyPI 相同）

### 4.2 配置 TestPyPI Token

创建或编辑 `~/.pypirc` 文件：

```bash
# macOS/Linux
nano ~/.pypirc

# Windows (在用户目录下创建 .pypirc 文件)
notepad %USERPROFILE%\.pypirc
```

添加以下内容：

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-你的正式PyPI-token

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-你的TestPyPI-token
```

**注意：**
- `__token__` 是固定值，不要修改
- `password` 后面是你的 API token（以 `pypi-` 开头）
- TestPyPI 和正式 PyPI 的 token 是不同的

### 4.3 上传到 TestPyPI

```bash
twine upload --repository testpypi dist/*
```

**输入提示：**
- 如果配置了 `~/.pypirc`，会自动使用配置的 token
- 如果没有配置，会提示输入用户名和密码

**成功输出：**
```
Uploading distributions to https://test.pypi.org/legacy/
Uploading aimino-0.1.0-py3-none-any.whl
100%|████████████████████| 123k/123k [00:05<00:00, 23.4kB/s]
Uploading aimino-0.1.0.tar.gz
100%|████████████████████| 89k/89k [00:03<00:00, 28.1kB/s]

View at:
https://test.pypi.org/project/aimino/0.1.0/
```

### 4.4 测试安装

在**新的虚拟环境**中测试安装：

```bash
# 创建新的测试环境
python -m venv test_env
source test_env/bin/activate  # Windows: test_env\Scripts\activate

# 从 TestPyPI 安装（注意：需要同时使用 TestPyPI 和正式 PyPI）
# 因为 TestPyPI 不包含所有依赖包，需要从正式 PyPI 获取依赖
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ aimino

# 验证安装
python -c "import aimino_frontend; print('安装成功！')"

# 测试命令行工具
aimino-napari --help
```

**重要说明：**
- TestPyPI 只包含你上传的包，不包含其他依赖包
- 使用 `--extra-index-url https://pypi.org/simple/` 让 pip 在找不到依赖时从正式 PyPI 获取
- 这样既能测试你的包，又能安装所有依赖

**如果测试成功，可以继续发布到正式 PyPI。**

---

## 五、正式发布

### 5.1 上传到正式 PyPI

```bash
# 确保在 aimino_frontend 目录下
twine upload dist/*
```

**或者明确指定仓库：**

```bash
twine upload --repository pypi dist/*
```

**成功输出：**
```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading aimino-0.1.0-py3-none-any.whl
100%|████████████████████| 123k/123k [00:05<00:00, 23.4kB/s]
Uploading aimino-0.1.0.tar.gz
100%|████████████████████| 89k/89k [00:03<00:00, 28.1kB/s]

View at:
https://pypi.org/project/aimino/0.1.0/
```

### 5.2 访问项目页面

发布成功后，访问：
- 项目主页：https://pypi.org/project/aimino/
- 版本页面：https://pypi.org/project/aimino/0.1.0/

---

## 六、验证发布

### 6.1 等待索引更新

PyPI 需要几分钟时间来更新索引，通常 1-5 分钟。

### 6.2 测试安装

在**新的虚拟环境**中测试：

```bash
# 创建新的测试环境
python -m venv verify_env
source verify_env/bin/activate  # Windows: verify_env\Scripts\activate

# 从 PyPI 安装
pip install aimino

# 验证安装
python -c "import aimino_frontend; print('安装成功！')"

# 测试命令行工具
aimino-napari --help

# 查看包信息
pip show aimino
```

**期望输出：**
```
Name: aimino
Version: 0.1.0
Summary: AIMinO Napari frontend application with command execution and agent client
...
```

---

## 七、常见问题

### 7.1 包名已被占用

**错误信息：**
```
HTTPError: 400 Client Error: This filename has already been used
```

**解决方案：**
1. 修改 `pyproject.toml` 中的包名（如 `aimino-napari`）
2. 重新构建和上传

### 7.2 版本号已存在

**错误信息：**
```
HTTPError: 400 Client Error: File already exists
```

**解决方案：**
1. 在 `pyproject.toml` 中更新版本号
2. 重新构建和上传

**注意：** PyPI 不允许覆盖已发布的版本，只能发布新版本。

### 7.3 认证失败

**错误信息：**
```
HTTPError: 401 Client Error: Unauthorized
```

**解决方案：**
1. 检查 `~/.pypirc` 文件中的 token 是否正确
2. 确认 token 没有过期或被撤销
3. 重新生成 token 并更新配置

### 7.4 依赖项找不到

**错误信息：**
```
ERROR: Could not find a version that satisfies the requirement xxx
```

**解决方案：**
1. 检查 `pyproject.toml` 中的依赖项名称是否正确
2. 确认所有依赖项都在 PyPI 上可用
3. 如果使用私有依赖，需要先发布它们

### 7.5 文件未包含在分发包中

**问题：** 某些文件没有被包含在分发包中

**解决方案：**
1. 检查 `MANIFEST.in` 文件
2. 确保需要包含的文件在 `MANIFEST.in` 中列出
3. 重新构建分发包

---

## 八、更新已发布的包

### 8.1 更新版本号

在 `pyproject.toml` 中更新版本号：

```toml
version = "0.1.1"  # 新版本号
```

### 8.2 更新 CHANGELOG（可选但推荐）

创建或更新 `CHANGELOG.md` 文件，记录版本变更：

```markdown
# Changelog

## [0.1.1] - 2024-12-06

### Fixed
- 修复了某个 bug

## [0.1.0] - 2024-12-05

### Added
- 初始发布
```

### 8.3 重新构建和上传

```bash
# 清理旧文件
rm -rf dist/ build/ *.egg-info/

# 重新构建
python -m build

# 验证
twine check dist/*

# 上传新版本
twine upload dist/*
```

### 8.4 标记 GitHub Release（可选）

如果项目在 GitHub 上：

1. 访问项目的 Releases 页面
2. 点击 "Draft a new release"
3. 填写：
   - **Tag**: `v0.1.1`
   - **Title**: `v0.1.1`
   - **Description**: 从 CHANGELOG 复制
4. 发布

---

## 📝 发布检查清单

在发布前，请确认：

- [ ] PyPI 账号已注册
- [ ] API Token 已创建并配置
- [ ] `pyproject.toml` 配置正确
- [ ] 版本号已更新
- [ ] 所有必需文件存在（README.md, LICENSE, MANIFEST.in）
- [ ] 包名可用（未被占用）
- [ ] 所有依赖项都在 PyPI 上可用
- [ ] 代码已测试通过
- [ ] 分发包已构建成功
- [ ] `twine check` 通过
- [ ] 已在 TestPyPI 测试安装成功
- [ ] 准备发布到正式 PyPI

---

## 🎉 发布成功后的步骤

1. **更新文档**：在项目 README 中添加安装说明
2. **通知用户**：如果有用户群或邮件列表，通知新版本发布
3. **监控反馈**：关注 PyPI 项目页面的反馈和问题

---

## 📚 参考资源

- [PyPI 官方文档](https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/)
- [Twine 文档](https://twine.readthedocs.io/)
- [Python 打包指南](https://packaging.python.org/)
- [语义化版本规范](https://semver.org/lang/zh-CN/)

---

**祝发布顺利！** 🚀

