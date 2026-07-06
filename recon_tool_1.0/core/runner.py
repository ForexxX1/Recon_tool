import asyncio
import subprocess
from pathlib import Path
import tempfile
import shutil
from core.installer import get_tool_path, TOOLS_DIR

async def run_command(cmd, args, input_data=None, timeout=120):
    proc = await asyncio.create_subprocess_exec(
        cmd, *args,
        stdin=asyncio.subprocess.PIPE if input_data else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(input_data), timeout=timeout)
        return stdout.decode(errors='ignore'), stderr.decode(errors='ignore'), proc.returncode
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return "", "Timeout", -1

async def run_subfinder(domain):
    cmd = get_tool_path("subfinder")
    if not cmd:
        return set()
    args = ["-d", domain, "-silent", "-t", "100"]
    out, err, code = await run_command(cmd, args)
    if code == 0:
        return set(filter(None, out.strip().splitlines()))
    return set()

async def run_assetfinder(domain):
    cmd = get_tool_path("assetfinder")
    if not cmd:
        return set()
    args = ["--subs-only", domain]
    out, err, code = await run_command(cmd, args)
    if code == 0:
        return set(filter(None, out.strip().splitlines()))
    return set()

async def run_amass_passive(domain):
    cmd = get_tool_path("amass")
    if not cmd:
        return set()
    args = ["enum", "-passive", "-d", domain, "-silent"]
    out, err, code = await run_command(cmd, args, timeout=300)
    if code == 0:
        return set(filter(None, out.strip().splitlines()))
    return set()

async def run_httpx(domains, mode="safe"):
    if not domains:
        return []
    cmd = get_tool_path("httpx")
    if not cmd:
        print("[!] httpx не найден в tools или PATH")
        return []

    # Настройки в зависимости от режима
    if mode == "safe":
        threads = "10"
        delay = "100ms"
    elif mode == "medium":
        threads = "30"
        delay = "50ms"
    elif mode == "fast":
        threads = "50"
        delay = "0ms"
    else:
        threads = "10"
        delay = "100ms"

    temp_file = "httpx_input.txt"
    with open(temp_file, "w") as f:
        f.write("\n".join(domains))

    args = [
        "-l", temp_file,
        "-silent",
        "-status-code",
        "-title",
        "-tech-detect",
        "-follow-redirects",
        "-threads", threads,
        "-delay", delay,
        "-no-color"
    ]

    out, err, code = await run_command(cmd, args, timeout=300)
    Path(temp_file).unlink(missing_ok=True)
    if err:
        print(f"[!] httpx stderr: {err}")
    if code != 0:
        print(f"[!] httpx завершился с кодом {code}, вывод: {out[:200]}")
        return []

    results = []
    for line in out.strip().splitlines():
        if not line:
            continue
        parts = line.split()
        if len(parts) < 1:
            continue
        domain = parts[0]
        status = "?"
        title = ""

        for idx, part in enumerate(parts):
            if part.startswith('[') and part.endswith(']') and part[1:-1].isdigit():
                status = part[1:-1]
                title = " ".join(parts[idx+1:]) if idx+1 < len(parts) else ""
                break

        if status == "?" and len(parts) >= 2 and parts[1].isdigit():
            status = parts[1]
            title = " ".join(parts[2:]) if len(parts) > 2 else ""

        if status == "?" and len(parts) > 1:
            title = " ".join(parts[1:])

        results.append({"domain": domain, "status": status, "title": title})
    return results

async def run_waymore(domain):
    cmd = shutil.which("waymore")
    if not cmd:
        print("[!] waymore не установлен. Установите: pip install waymore")
        return []
    temp_name = f"waymore_{domain}.txt"
    args = ["-i", domain, "-oU", temp_name]
    out, err, code = await run_command(cmd, args, timeout=600)
    if err:
        print(f"[!] waymore stderr: {err}")
    urls = []
    if Path(temp_name).exists():
        try:
            with open(temp_name, "r", encoding="utf-8") as f:
                urls = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"[!] Ошибка чтения файла: {e}")
        Path(temp_name).unlink(missing_ok=True)
    else:
        print("[!] Файл не создан")
    urls = list(set(urls))[:2000] if len(urls) > 2000 else list(set(urls))
    return urls
