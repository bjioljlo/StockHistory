#!/usr/bin/env bash
# ensure-glab.sh
# 偵測 glab 是否已安裝，若無則依據 OS 自動安裝
# 回傳碼：0 = 成功，1 = 失敗

set -e

echo "🔍 正在確認 glab 安裝狀態..."

if command -v glab &>/dev/null; then
  VERSION=$(glab --version | head -n1)
  echo "✅ glab 已安裝：$VERSION"
  exit 0
fi

echo "⚠️  找不到 glab，開始自動安裝..."

OS="$(uname -s)"
ARCH="$(uname -m)"

install_macos() {
  if command -v brew &>/dev/null; then
    echo "📦 使用 Homebrew 安裝 glab..."
    brew install glab
  else
    echo "❌ 找不到 Homebrew。請先安裝 Homebrew："
    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
  fi
}

install_linux() {
  # 嘗試偵測套件管理器
  if command -v apt-get &>/dev/null; then
    echo "📦 使用 apt 安裝 glab..."
    curl -fsSL https://gitlab.com/gitlab-org/cli/-/raw/main/scripts/install.sh | sh
  elif command -v dnf &>/dev/null; then
    echo "📦 使用 dnf 安裝 glab..."
    sudo dnf install -y glab
  elif command -v yum &>/dev/null; then
    echo "📦 使用 yum 安裝 glab..."
    sudo yum install -y glab
  elif command -v pacman &>/dev/null; then
    echo "📦 使用 pacman 安裝 glab..."
    sudo pacman -S --noconfirm gitlab-glab-bin 2>/dev/null || \
    sudo pacman -S --noconfirm glab
  else
    # fallback: 直接下載 binary
    echo "📦 直接下載 glab binary..."
    install_binary_linux
  fi
}

install_binary_linux() {
  LATEST=$(curl -fsSL "https://gitlab.com/api/v4/projects/gitlab-org%2Fcli/releases" | \
    grep '"tag_name"' | head -1 | sed 's/.*"tag_name": "v\([^"]*\)".*/\1/')

  if [ -z "$LATEST" ]; then
    echo "❌ 無法取得 glab 最新版本號，請手動安裝："
    echo "   https://gitlab.com/gitlab-org/cli#installation"
    exit 1
  fi

  case "$ARCH" in
    x86_64) ARCH_NAME="amd64" ;;
    aarch64|arm64) ARCH_NAME="arm64" ;;
    *) echo "❌ 不支援的架構：$ARCH"; exit 1 ;;
  esac

  DOWNLOAD_URL="https://gitlab.com/gitlab-org/cli/-/releases/v${LATEST}/downloads/glab_${LATEST}_linux_${ARCH_NAME}.tar.gz"
  TMP_DIR=$(mktemp -d)

  echo "⬇️  下載 glab v${LATEST}..."
  curl -fsSL "$DOWNLOAD_URL" -o "$TMP_DIR/glab.tar.gz"
  tar -xzf "$TMP_DIR/glab.tar.gz" -C "$TMP_DIR"

  INSTALL_DIR="/usr/local/bin"
  if [ ! -w "$INSTALL_DIR" ]; then
    INSTALL_DIR="$HOME/.local/bin"
    mkdir -p "$INSTALL_DIR"
    echo "ℹ️  安裝至 $INSTALL_DIR（需確認此路徑在 PATH 中）"
  fi

  mv "$TMP_DIR/bin/glab" "$INSTALL_DIR/glab"
  chmod +x "$INSTALL_DIR/glab"
  rm -rf "$TMP_DIR"
}

install_windows() {
  if command -v winget &>/dev/null; then
    echo "📦 使用 winget 安裝 glab..."
    # 正確的 package ID 為 GLab.GLab，需明確指定 --source winget
    # （winget search 顯示 GLab.GLab，使用 Gitlab.Glab 或省略 --source 會找不到套件）
    winget install --id GLab.GLab -e --source winget
  elif command -v choco &>/dev/null; then
    echo "📦 使用 Chocolatey 安裝 glab..."
    choco install glab
  elif command -v scoop &>/dev/null; then
    echo "📦 使用 Scoop 安裝 glab..."
    scoop install glab
  else
    echo "❌ 找不到支援的套件管理器（winget / choco / scoop）"
    echo "   請手動安裝：https://gitlab.com/gitlab-org/cli#installation"
    exit 1
  fi
}

# 依作業系統執行對應安裝
case "$OS" in
  Darwin) install_macos ;;
  Linux)  install_linux ;;
  MINGW*|MSYS*|CYGWIN*) install_windows ;;
  *)
    echo "❌ 不支援的作業系統：$OS"
    echo "   請手動安裝：https://gitlab.com/gitlab-org/cli#installation"
    exit 1
    ;;
esac

# 確認安裝成功
if command -v glab &>/dev/null; then
  VERSION=$(glab --version | head -n1)
  echo "✅ glab 安裝成功：$VERSION"
else
  echo "❌ glab 安裝後仍無法執行，請確認 PATH 設定"
  echo "   嘗試重新開啟終端機，或手動將安裝路徑加入 PATH"
  exit 1
fi
