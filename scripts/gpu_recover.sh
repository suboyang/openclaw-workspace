#!/usr/bin/env bash
set -euo pipefail

# GPU 恢復腳本（針對 NVIDIA A2000 / GDM 關閉常態）
# 用途：當 nvidia-smi 報 Unknown Error / No devices were found 時，嘗試自動恢復驅動
# 設計原則：
# 1. 預設不啟動 GDM
# 2. 先做最小恢復（重啟 nvidia-persistenced / 重新載入模組）
# 3. 必要時提示使用者重開機

log() {
  echo "[$(date '+%F %T')] $*"
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "缺少命令: $1" >&2
    exit 1
  }
}

check_gpu() {
  nvidia-smi >/tmp/gpu_recover_nvidia_smi.log 2>&1
}

show_last_error() {
  if [ -f /tmp/gpu_recover_nvidia_smi.log ]; then
    echo "--- nvidia-smi 輸出 ---"
    cat /tmp/gpu_recover_nvidia_smi.log
    echo "------------------------"
  fi
}

stop_display_stack() {
  log "停止顯示相關服務（如果有）..."
  sudo systemctl stop gdm3 2>/dev/null || true
  sudo systemctl stop display-manager 2>/dev/null || true
  sleep 2
}

try_restart_persistenced() {
  log "嘗試重啟 nvidia-persistenced..."
  sudo systemctl restart nvidia-persistenced 2>/dev/null || true
  sleep 2
}

reload_nvidia_modules() {
  log "重新載入 NVIDIA 核心模組..."
  sudo modprobe -r nvidia_drm nvidia_modeset nvidia_uvm nvidia 2>/dev/null || true
  sleep 2
  sudo modprobe nvidia
  sudo modprobe nvidia_uvm
  sudo modprobe nvidia_modeset
  sudo modprobe nvidia_drm
  sleep 3
}

print_status() {
  echo
  log "目前 GPU / 驅動狀態："
  nvidia-smi || true
  echo
  lsmod | grep '^nvidia' || true
  echo
  lspci -nnk | grep -A3 -E 'VGA|3D|Display' || true
}

need_cmd nvidia-smi
need_cmd lspci
need_cmd lsmod
need_cmd modprobe
need_cmd systemctl

log "開始檢查 NVIDIA GPU 狀態..."
if check_gpu; then
  log "GPU 正常，無需恢復。"
  cat /tmp/gpu_recover_nvidia_smi.log
  exit 0
fi

log "檢測到 GPU 異常，開始恢復流程。"
show_last_error

stop_display_stack
try_restart_persistenced

log "第一次快速檢查..."
if check_gpu; then
  log "GPU 已恢復（重啟 persistenced 後成功）。"
  cat /tmp/gpu_recover_nvidia_smi.log
  exit 0
fi

reload_nvidia_modules

log "第二次檢查..."
if check_gpu; then
  log "GPU 已恢復（模組重載後成功）。"
  cat /tmp/gpu_recover_nvidia_smi.log
  exit 0
fi

log "仍未恢復，輸出目前狀態供排查。"
show_last_error
print_status

echo
echo "⚠️  GPU 仍未恢復。建議下一步："
echo "1. sudo reboot"
echo "2. 開機後不要啟動 GDM，先測 nvidia-smi"
echo "3. 若仍失敗，再檢查 dmesg / journalctl -k | grep -i nvrm"
exit 1
