#!/bin/bash
# 远程Hermes实例旧权限系统一键清理脚本
# 使用方式: ./remote_permission_cleanup.sh <ssh_host> <ssh_user> <ssh_password>

set -e

if [ $# -ne 3 ]; then
    echo "❌ 参数错误！使用方式: $0 <SSH地址> <SSH账号> <SSH密码>"
    exit 1
fi

SSH_HOST=$1
SSH_USER=$2
SSH_PASS=$3

echo "🚀 开始清理远程实例 $SSH_HOST 旧权限系统残留..."

# 检查sshpass是否已安装
if ! command -v sshpass &> /dev/null; then
    echo "🔧 安装sshpass依赖..."
    apt update && apt install -y sshpass
fi

# 远程执行清理操作
sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 $SSH_USER@$SSH_HOST '
echo "  1/6 删除权限相关技能目录..."
find ~/.hermes/skills -type d \( -name "*permission-governance*" -o -name "*permission-management*" \) | xargs rm -rf 2>/dev/null || true

echo "  2/6 删除权限Hook目录..."
rm -rf ~/.hermes/hooks/permission* 2>/dev/null || true

echo "  3/6 删除权限配置文件（含备份）..."
rm -f ~/.hermes/permission-config.yaml ~/.hermes/permission-config.yaml.bak* 2>/dev/null || true

echo "  4/6 删除权限相关日志..."
rm -f ~/.hermes/logs/permission-*.log 2>/dev/null || true

echo "  5/6 清理config.yaml中的权限Hook配置..."
sed -i '/^ *pre_tool_call:/,/^ *.*timeout: *[0-9]*/d' ~/.hermes/config.yaml
sed -i '/^ *gateway:/,/^ *.*timeout: *[0-9]*/d' ~/.hermes/config.yaml
sed -i '/^ *skills:/,/^ *.*timeout: *[0-9]*/d' ~/.hermes/config.yaml
sed -i '/^ *tools:/,/^ *.*timeout: *[0-9]*/d' ~/.hermes/config.yaml

echo "  6/6 重启网关生效..."
systemctl --user restart hermes-gateway.service 2>/dev/null || true
'

echo "✅ 远程实例 $SSH_HOST 旧权限系统清理完成！网关已重启。"
