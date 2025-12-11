#!/bin/bash
# PyPI 发布脚本
# 使用方法: ./publish.sh [test|prod]

set -e  # 遇到错误立即退出

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== AIMinO PyPI 发布脚本 ===${NC}\n"

# 检查参数
REPO=${1:-test}
if [[ "$REPO" != "test" && "$REPO" != "prod" ]]; then
    echo -e "${RED}错误: 参数必须是 'test' 或 'prod'${NC}"
    echo "使用方法: ./publish.sh [test|prod]"
    exit 1
fi

# 检查必要工具
echo -e "${YELLOW}检查构建工具...${NC}"
if ! command -v python &> /dev/null; then
    echo -e "${RED}错误: 未找到 python${NC}"
    exit 1
fi

# 安装构建工具（如果需要）
if ! python -c "import build" 2>/dev/null; then
    echo -e "${YELLOW}安装 build 工具...${NC}"
    pip install build twine
fi

# 读取版本号
VERSION=$(grep -E '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
PACKAGE_NAME=$(grep -E '^name = ' pyproject.toml | sed 's/name = "\(.*\)"/\1/')

echo -e "${GREEN}包名: ${PACKAGE_NAME}${NC}"
echo -e "${GREEN}版本: ${VERSION}${NC}\n"

# 清理旧的构建文件
echo -e "${YELLOW}清理旧的构建文件...${NC}"
rm -rf dist/ build/ *.egg-info/

# 构建分发包
echo -e "${YELLOW}构建分发包...${NC}"
python -m build

# 验证分发包
echo -e "${YELLOW}验证分发包...${NC}"
if ! twine check dist/*; then
    echo -e "${RED}错误: 分发包验证失败${NC}"
    exit 1
fi

# 显示构建的文件
echo -e "\n${GREEN}构建的文件:${NC}"
ls -lh dist/

# 确认发布
if [[ "$REPO" == "prod" ]]; then
    echo -e "\n${YELLOW}⚠️  警告: 即将发布到正式 PyPI!${NC}"
    read -p "确认发布到正式 PyPI? (yes/no): " confirm
    if [[ "$confirm" != "yes" ]]; then
        echo -e "${YELLOW}已取消发布${NC}"
        exit 0
    fi
    echo -e "${YELLOW}上传到正式 PyPI...${NC}"
    twine upload dist/*
    echo -e "\n${GREEN}✅ 发布成功!${NC}"
    echo -e "${GREEN}项目页面: https://pypi.org/project/${PACKAGE_NAME}/${VERSION}/${NC}"
else
    echo -e "${YELLOW}上传到 TestPyPI...${NC}"
    twine upload --repository testpypi dist/*
    echo -e "\n${GREEN}✅ 测试发布成功!${NC}"
    echo -e "${GREEN}项目页面: https://test.pypi.org/project/${PACKAGE_NAME}/${VERSION}/${NC}"
    echo -e "\n${YELLOW}测试安装命令:${NC}"
    echo "pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ ${PACKAGE_NAME}"
fi

echo -e "\n${GREEN}完成!${NC}"

