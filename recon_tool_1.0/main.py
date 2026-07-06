#!/usr/bin/env python3
import asyncio
import argparse
from core.installer import ensure_tools
from core.runner import run_subfinder, run_assetfinder, run_amass_passive, run_httpx, run_waymore
from core.collectors import fetch_crtsh, fetch_dnsdumpster
from core.report import generate_report
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

async def recon(domain, mode):
    console.print(f"[bold cyan]Начинаем разведку для {domain}[/]")
    console.print(f"[bold yellow]Режим httpx: {mode}[/]")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task1 = progress.add_task("[yellow]Сбор поддоменов (subfinder, assetfinder, crt.sh, dnsdumpster)...", total=None)
        tasks = [
            run_subfinder(domain),
            run_assetfinder(domain),
            fetch_crtsh(domain),
            fetch_dnsdumpster(domain)
        ]
        results = await asyncio.gather(*tasks)
        subfinder_set, assetfinder_set, crtsh_set, dnsdumpster_set = results
        all_domains = subfinder_set | assetfinder_set | crtsh_set | dnsdumpster_set
        all_domains.add(domain)
        progress.update(task1, completed=True)

        task2 = progress.add_task("[yellow]Amass (пассивный режим)...", total=None)
        amass_set = await run_amass_passive(domain)
        all_domains |= amass_set
        progress.update(task2, completed=True)

    console.print(f"[green]Найдено {len(all_domains)} уникальных поддоменов[/]")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task3 = progress.add_task("[yellow]Проверка живых хостов (httpx)...", total=None)
        alive = await run_httpx(list(all_domains), mode)
        progress.update(task3, completed=True)
    console.print(f"[green]Обнаружено {len(alive)} живых хостов[/]")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task4 = progress.add_task("[yellow]Сбор исторических URL (waymore)...", total=None)
        urls = await run_waymore(domain)
        progress.update(task4, completed=True)
    console.print(f"[green]Найдено {len(urls)} URL-адресов[/]")

    if not isinstance(alive, list):
        alive = []
    else:
        alive = [h for h in alive if isinstance(h, dict) and "domain" in h]

    report_data = {
        "subdomains": list(all_domains),
        "alive": alive,
        "urls": urls
    }
    return report_data

async def main():
    parser = argparse.ArgumentParser(description="OSINT Recon Tool")
    parser.add_argument("domain", nargs="?", help="Target domain (e.g., example.com)")
    parser.add_argument("--mode", "-m", choices=["safe", "fast", "medium"], default="safe",
                        help="Mode for httpx: safe (10 threads, 100ms delay), fast (50 threads, 0 delay), medium (30 threads, 50ms delay)")
    args = parser.parse_args()

    if not args.domain:
        target = input("Введите домен (например, example.com): ").strip()
    else:
        target = args.domain

    if not target:
        console.print("[red]Домен не указан.[/]")
        return

    console.print("[bold]Проверка инструментов...[/]")
    ensure_tools()

    data = await recon(target, args.mode)
    generate_report(data, target)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("[red]Прервано пользователем[/]")
