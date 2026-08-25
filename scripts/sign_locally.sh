#!/bin/bash
# sign_locally.sh
# 用途:在 Mac 上为 GitHub Actions 产出的 unsigned IPA 重签 + 安装到 iPhone
#
# 前置条件(只需做一次):
#   1. 安装 Xcode 14+ 并打开一次(同意许可)
#   2. Xcode → Settings → Accounts → 添加你的 Apple ID(免费账号即可)
#   3. 用 Xcode 新建一个空的 iOS App 工程,Bundle ID 填 org.local.sudoku,
#      Team 选你的 Apple ID,Build 一次(失败也行,Xcode 会自动生成证书和 profile)
#   4. 用 USB 连接 iPhone,在 Xcode → Window → Devices and Simulators 中确认设备可见
#
# 用法:
#   chmod +x sign_locally.sh
#   ./sign_locally.sh sudoku-unsigned.ipa
#
# 流程:解压 IPA → 用本地 Apple Development 证书重签 → 重新打包 → 安装到设备

set -euo pipefail

# ============= 参数检查 =============
if [ $# -lt 1 ]; then
    echo "用法: $0 <unsigned.ipa> [设备 UDID]"
    echo "  示例: $0 sudoku-unsigned.ipa"
    echo "  示例: $0 sudoku-unsigned.ipa 00008110-XXXXYYYY"
    exit 1
fi

IPA_IN="$1"
DEVICE_UDID="${2:-}"

if [ ! -f "$IPA_IN" ]; then
    echo "[ERROR] 未找到 IPA 文件: $IPA_IN"
    exit 1
fi

# ============= 检测签名证书 =============
echo "[1/5] 检测可用签名证书..."
CERT_LINE=$(security find-identity -p codesigning -v | grep "Apple Development" | head -1 || true)
if [ -z "$CERT_LINE" ]; then
    echo "[ERROR] 未找到 Apple Development 证书"
    echo "  请先在 Xcode 中登录 Apple ID 并 Build 一次任意 iOS 工程"
    exit 1
fi
# 提取引号内的证书名
CERT_NAME=$(echo "$CERT_LINE" | sed 's/.*"\(.*\)".*/\1/')
echo "  -> 使用证书: $CERT_NAME"

# 从证书名中提取 Team ID(括号里的 10 位字符)
TEAM_ID=$(echo "$CERT_NAME" | grep -oE '\([A-Z0-9]{10}\)' | tr -d '()' || true)
if [ -z "$TEAM_ID" ]; then
    echo "[ERROR] 无法从证书名提取 Team ID: $CERT_NAME"
    echo "  请检查证书格式,或手动指定"
    exit 1
fi
echo "  -> Team ID: $TEAM_ID"

# ============= 查找 Provisioning Profile =============
echo "[2/5] 查找 Provisioning Profile..."
PP_DIR="$HOME/Library/MobileDevice/Provisioning Profiles"
if [ ! -d "$PP_DIR" ]; then
    echo "[ERROR] 未找到 Provisioning Profiles 目录"
    echo "  请先用 Xcode Build 一次 iOS 工程,让 Xcode 自动生成 profile"
    exit 1
fi

# 找到包含 org.local.sudoku 的 profile
PROFILE=$(find "$PP_DIR" -name "*.mobileprovision" -newer "$PP_DIR" 2>/dev/null | while read f; do
    # 解析 profile 内容,匹配 application-identifier
    if security cms -D -i "$f" 2>/dev/null | grep -q "org.local.sudoku"; then
        echo "$f"
        break
    fi
done | head -1)

if [ -z "$PROFILE" ]; then
    echo "[ERROR] 未找到包含 org.local.sudoku 的 Provisioning Profile"
    echo "  请确认 Xcode 工程的 Bundle ID 是 org.local.sudoku"
    exit 1
fi
echo "  -> 使用 profile: $(basename "$PROFILE")"

# ============= 解压 IPA =============
echo "[3/5] 解压 IPA..."
WORK_DIR=$(mktemp -d)
trap "rm -rf $WORK_DIR" EXIT
unzip -q "$IPA_IN" -d "$WORK_DIR"

APP_DIR="$WORK_DIR/Payload/sudoku.app"
if [ ! -d "$APP_DIR" ]; then
    echo "[ERROR] IPA 内未找到 Payload/sudoku.app"
    exit 1
fi

# ============= 重签 =============
echo "[4/5] 重签应用..."
# 复制 provisioning profile 到 .app
cp "$PROFILE" "$APP_DIR/embedded.mobileprovision"

# 生成 entitlements.plist
ENT_FILE="$WORK_DIR/entitlements.plist"
cat > "$ENT_FILE" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>get-task-allow</key>
    <true/>
    <key>application-identifier</key>
    <string>${TEAM_ID}.org.local.sudoku</string>
    <key>com.apple.developer.team-identifier</key>
    <string>${TEAM_ID}</string>
</dict>
</plist>
EOF

# 修改 Info.plist 中的 CFBundleIdentifier(确保与 profile 匹配)
plutil -replace CFBundleIdentifier -string "org.local.sudoku" "$APP_DIR/Info.plist" 2>/dev/null || true

# 签名
codesign -f -s "$CERT_NAME" --entitlements "$ENT_FILE" "$APP_DIR"
echo "  -> 签名完成"

# 重新打包 IPA
SIGNED_IPA="${IPA_IN%.ipa}-signed.ipa"
cd "$WORK_DIR"
zip -qry "$SIGNED_IPA" Payload
echo "  -> 生成: $SIGNED_IPA"
ls -lh "$SIGNED_IPA"

# ============= 安装到设备 =============
if [ -z "$DEVICE_UDID" ]; then
    echo "[5/5] 未指定设备 UDID,跳过自动安装"
    echo "  手动安装方式:"
    echo "    1. 用 USB 连接 iPhone,在 Xcode → Window → Devices and Simulators 查看 UDID"
    echo "    2. 重新运行: $0 $IPA_IN <UDID>"
    echo "    或:用 Xcode 的 Devices 窗口拖拽 IPA 安装"
    exit 0
fi

echo "[5/5] 安装到设备 $DEVICE_UDID..."
# Xcode 15+ 用 devicectl
if command -v xcrun devicectl >/dev/null 2>&1; then
    xcrun devicectl device install app --device "$DEVICE_UDID" "$SIGNED_IPA"
elif command -v ios-deploy >/dev/null 2>&1; then
    ios-deploy --bundle "$APP_DIR"
else
    echo "[WARN] 未找到 devicectl 或 ios-deploy"
    echo "  请用 Xcode → Window → Devices and Simulators 拖拽 IPA 安装"
fi

echo ""
echo "================================================"
echo "完成!请在 iPhone 上:"
echo "  设置 → 通用 → VPN与设备管理 → 信任开发者"
echo "================================================"
