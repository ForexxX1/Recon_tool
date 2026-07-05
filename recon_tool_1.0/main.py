#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path
from core.installer import ensure_tools
from core.runner import run_subfinder, run_assetfinder, run_amass_passive, run_httpx, run_waymore
from core.collectors import fetch_crtsh, fetch_dnsdumpster
from core.report import generate_report
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

async def recon(domain):
    console.print(f"[bold cyan]Начинаем разведку для {domain}[/]")

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
        alive = await run_httpx(list(all_domains))
        progress.update(task3, completed=True)
    console.print(f"[green]Обнаружено {len(alive)} живых хостов[/]")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task4 = progress.add_task("[yellow]Сбор исторических URL (waymore)...", total=None)
        urls = await run_waymore(domain)
        progress.update(task4, completed=True)
    console.print(f"[green]Найдено {len(urls)} URL-адресов[/]")

    # Защита от мусора в alive
    if not isinstance(alive, list):
        alive = []
    else:
        # Оставляем только элементы, которые являются словарями с ключом "domain"
        alive = [h for h in alive if isinstance(h, dict) and "domain" in h]

    report_data = {
        "subdomains": list(all_domains),
        "alive": alive,
        "urls": urls
    }
    return report_data

async def main():
    if len(sys.argv) < 2:
        target = input("Введите домен (например, example.com): ").strip()
    else:
        target = sys.argv[1]

    if not target:
        console.print("[red]Домен не указан.[/]")
        return

    console.print("[bold]Проверка инструментов...[/]")
    ensure_tools()

    data = await recon(target)
    generate_report(data, target)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("[red]Прервано пользователем[/]")
