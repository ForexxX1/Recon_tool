import json
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

BASE_DIR = Path(__file__).parent.parent
TEMPLATE_DIR = BASE_DIR / "templates"

def generate_report(data, target):
    # сохраняем JSON
    json_path = BASE_DIR / f"report_{target}.json"
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    
    # генерируем HTML
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("report.html")
    html_content = template.render(
        data=data,
        target=target,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    html_path = BASE_DIR / f"report_{target}.html"
    with open(html_path, "w") as f:
        f.write(html_content)
    
    print(f"[+] Отчёт сохранён: {html_path} и {json_path}")
    return html_path, json_path
