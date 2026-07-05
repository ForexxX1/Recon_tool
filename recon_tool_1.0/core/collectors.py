import aiohttp
import asyncio
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse

async def fetch_crtsh(domain):
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    subdomains = set()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for entry in data:
                        name = entry.get("name_value", "")
                        if name and (name.endswith(domain) or name.endswith("." + domain)):
                            clean = name.strip().lower()
                            if clean.startswith("*."):
                                clean = clean[2:]
                            subdomains.add(clean)
    except:
        pass
    return subdomains

async def fetch_dnsdumpster(domain):
    subdomains = set()
    try:
        async with aiohttp.ClientSession() as session:
            # сначала GET для получения CSRF-токена
            async with session.get("https://dnsdumpster.com/", timeout=20) as resp:
                html = await resp.text()
                soup = BeautifulSoup(html, "html.parser")
                csrf = soup.find("input", {"name": "csrfmiddlewaretoken"})
                if not csrf:
                    return subdomains
                token = csrf.get("value")
                # POST запрос
                data = {
                    "csrfmiddlewaretoken": token,
                    "targetip": domain
                }
                headers = {"Referer": "https://dnsdumpster.com/"}
                async with session.post("https://dnsdumpster.com/", data=data, headers=headers, timeout=30) as post_resp:
                    html_result = await post_resp.text()
                    soup_result = BeautifulSoup(html_result, "html.parser")
                    # таблица с поддоменами обычно находится в классе table
                    tables = soup_result.find_all("table")
                    if tables:
                        # обычно первая таблица содержит поддомены
                        rows = tables[0].find_all("tr")
                        for row in rows:
                            cols = row.find_all("td")
                            if len(cols) >= 1:
                                # первый столбец – поддомен
                                sub = cols[0].get_text(strip=True)
                                if sub and sub != domain:
                                    subdomains.add(sub)
    except Exception as e:
        print(f"DNSDumpster error: {e}")
    return subdomains
