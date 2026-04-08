import subprocess
import time
import os
import json
import socket
import datetime
import psutil
import requests

# --- 配置区 ---
TARGET_CHANNEL_ID = "1486326928578183270" 
CONFIG_PATH = os.path.expanduser("~/.openclaw/openclaw.json")
NAS_PATH = "/mnt/nas_data"
MAX_RETRIES = 10  # 最多检查10次
RETRY_INTERVAL = 5 # 每次间隔5秒

#def check_gateway_status():
#    """执行指令并检查 RPC probe 是否为 ok"""
#    try:
#        # 执行 status 命令并获取输出
#        result = subprocess.check_output(["openclaw", "gateway", "status"], stderr=subprocess.STDOUT).decode('utf-8')
#        
#        # 核心检查点：Runtime 必须是 running，RPC probe 必须是 ok
#        if "Runtime: running" in result and "RPC probe: ok" in result:
#            return True, result
#        return False, result
#    except Exception as e:
#        return False, str(e)

def check_gateway_status():
    """使用绝对路径执行指令"""
    # 强制指定 openclaw 的位置
    OPENCLAW_BIN = "/home/openclaw/.npm-global/bin/openclaw"
    
    try:
        # 使用绝对路径运行
        result = subprocess.check_output(
            [OPENCLAW_BIN, "gateway", "status"], 
            stderr=subprocess.STDOUT,
            env={**os.environ, "PATH": "/home/openclaw/.npm-global/bin:" + os.environ["PATH"]}
        ).decode('utf-8')

        if "Runtime: running" in result and "RPC probe: ok" in result:
            return True, result
        return False, f"Output not match: {result[:50]}" # 打印前50个字符方便调试
    except Exception as e:
        return False, f"Exec error: {str(e)}"



def load_config():
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
            token = config.get("channels", {}).get("discord", {}).get("token")
            return token
    except:
        return None

def get_power_profile():
    try:
        profile = subprocess.check_output(["powerprofilesctl", "get"], stderr=subprocess.STDOUT).decode().strip()
        return profile or "未知"
    except Exception:
        return "未知"


def get_gpu_status():
    try:
        name = subprocess.check_output([
            "nvidia-smi", "--query-gpu=name", "--format=csv,noheader"
        ], stderr=subprocess.STDOUT).decode().strip().splitlines()[0]
        mem = subprocess.check_output([
            "nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"
        ], stderr=subprocess.STDOUT).decode().strip().splitlines()[0]
        util = subprocess.check_output([
            "nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"
        ], stderr=subprocess.STDOUT).decode().strip().splitlines()[0]
        used, total = [x.strip() for x in mem.split(',')]
        return f"✅ {name} | {used}/{total} MB | 利用率 {util}%"
    except Exception as e:
        return f"❌ 不可用 ({str(e)[:80]})"


def get_sys_info():
    hostname = socket.gethostname()
    now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    uptime = f"{int((time.time() - psutil.boot_time()) // 3600)}h"
    load_avg = os.getloadavg()[0]
    disk = psutil.disk_usage('/')
    nas_status = "✅ 已连接" if os.path.ismount(NAS_PATH) else "❌ 未挂载"
    power_profile = get_power_profile()
    gpu_status = get_gpu_status()

    return (
        "🧸✨ **台台小助手上线通知**\n\n"
        f"💻 **主机名**: `{hostname}`\n"
        f"🕐 **上线时间**: {now_time}\n"
        f"⏱️ **运行时长**: {uptime}\n"
        f"📊 **系统负载**: {load_avg}\n"
        f"💾 **根分区使用**: {disk.percent}% (1TB)\n"
        f"⚙️ **性能模式**: {power_profile}\n"
        f"🎮 **GPU 状态**: {gpu_status}\n"
        f"📂 **NAS 状态**: {nas_status}\n"
        f"⚡ **Gateway 状态**: ✅ 正常运行 (RPC OK)\n\n"
        f"🔗 **控制面板**: http://192.168.180.159:18789/\n"
        "> 报告 Master，所有系统组件已就绪！"
    )

def send_to_discord(token, message):
    url = f"https://discord.com/api/v10/channels/{TARGET_CHANNEL_ID}/messages"
    headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}
    requests.post(url, headers=headers, json={"content": message})

if __name__ == "__main__":
    print("🧸 正在启动状态监控检查...")
    
    success = False
    for i in range(MAX_RETRIES):
        is_ok, output = check_gateway_status()
        if is_ok:
            print(f"✅ 第 {i+1} 次检查：Gateway 已就绪！")
            success = True
            break
        else:
            print(f"⏳ 第 {i+1} 次检查：Gateway 尚未就绪，等待中...")
            time.sleep(RETRY_INTERVAL)

    if success:
        token = load_config()
        if token:
            send_to_discord(token, get_sys_info())
        else:
            print("❌ 错误：无法从 openclaw.json 读取 Token")
    else:
        print("❌ 达到最大尝试次数，Gateway 启动超时或异常。")
