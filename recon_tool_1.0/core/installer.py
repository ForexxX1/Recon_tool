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
    # Сначала ищем в папке tools/
    local_path = TOOLS_DIR / name
    if local_path.exists():
        return str(local_path)
    # Потом в системном PATH
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

        # Рекурсивно ищем бинарник в ~/go/bin и подпапках
        go_bin_dir = os.path.expanduser("~/go/bin")
        found = False
        if os.path.isdir(go_bin_dir):
            for root, dirs, files in os.walk(go_bin_dir):
                if name in files:
                    src = os.path.join(root, name)
                    shutil.copy(src, TOOLS_DIR / name)
                    os.chmod(TOOLS_DIR / name, 0o755)
                    print(f"[+] {name} найден в {root} и скопирован в tools/")
                    found = True
                    break

        if not found:
            print(f"[-] Бинарник {name} не найден в ~/go/bin (и подпапках)")
            return False
        return True
    except Exception as e:
        print(f"[-] Ошибка установки {name}: {e}")
        return False

def ensure_waymore():
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

    # Проверяем наличие каждой утилиты
    for name, info in deps.items():
        if not check_tool(name, info["check_cmd"]):
            missing.append(name)

    if missing:
        print(f"[!] Отсутствуют: {', '.join(missing)}. Устанавливаю...")
        for name in missing:
            install_tool(name, deps[name]["install_cmd"])
    else:
        print("[+] Все инструменты уже установлены.")

    # Дополнительно: если бинарник есть в ~/go/bin, но не скопирован в tools/ — копируем
    go_bin_dir = os.path.expanduser("~/go/bin")
    if os.path.isdir(go_bin_dir):
        for name in deps.keys():
            if not (TOOLS_DIR / name).exists():
                # ищем рекурсивно
                for root, dirs, files in os.walk(go_bin_dir):
                    if name in files:
                        src = os.path.join(root, name)
                        shutil.copy(src, TOOLS_DIR / name)
                        os.chmod(TOOLS_DIR / name, 0o755)
                        print(f"[+] {name} скопирован в tools/ из {root}")
                        break

    # Устанавливаем waymore через pip (если ещё нет)
    ensure_waymore()
