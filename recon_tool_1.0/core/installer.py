import json
import os
import subprocess
import shutil
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
TOOLS_DIR = BASE_DIR / "tools"
DEPS_FILE = BASE_DIR / "deps.json"

def ensure_tools_dir():
    TOOLS_DIR.mkdir(exist_ok=True)

def load_deps():
    with open(DEPS_FILE) as f:
        return json.load(f)["tools"]

def get_tool_path(name):
    local_path = TOOLS_DIR / name
    if local_path.exists():
        return str(local_path)
    system_path = shutil.which(name)
    if system_path:
        return system_path
    return None

def check_tool(name, check_cmd):
    path = get_tool_path(name)
    if not path:
        return False
    try:
        subprocess.run(check_cmd.split(), capture_output=True, timeout=10, check=False)
        return True
    except:
        return False

def install_tool(name, install_cmd):
    print(f"[*] Установка {name}...")
    try:
        subprocess.run(install_cmd, shell=True, check=True, timeout=300)
        go_bin = os.path.expanduser(f"~/go/bin/{name}")
        if os.path.exists(go_bin):
            shutil.copy(go_bin, TOOLS_DIR / name)
            os.chmod(TOOLS_DIR / name, 0o755)
        print(f"[+] {name} установлен.")
        return True
    except Exception as e:
        print(f"[-] Ошибка установки {name}: {e}")
        return False

def ensure_waymore():
    """Проверяет наличие waymore, устанавливает через pip если отсутствует."""
    if shutil.which("waymore") is None:
        print("[!] waymore не найден. Устанавливаю через pip...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "waymore"], check=True, timeout=120)
            print("[+] waymore установлен.")
            return True
        except Exception as e:
            print(f"[-] Ошибка установки waymore: {e}")
            return False
    return True

def ensure_tools():
    ensure_tools_dir()
    deps = load_deps()
    missing = []
    for name, info in deps.items():
        if not check_tool(name, info["check_cmd"]):
            missing.append(name)
    if missing:
        print(f"[!] Отсутствуют: {', '.join(missing)}. Устанавливаю...")
        for name in missing:
            install_tool(name, deps[name]["install_cmd"])
    else:
        print("[+] Все инструменты уже установлены.")
    # Дополнительно проверяем waymore
    ensure_waymore()
