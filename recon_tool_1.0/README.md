# Recon Tool – Passive Data Gathering

Automated tool for passive information gathering about web applications and domains. Finds subdomains, checks live hosts, collects historical URLs, and generates a clean HTML/JSON report.

**Important:** Use only on domains for which you have explicit written permission from the owner. Misuse is your own responsibility.

---

## Features

- **Passive subdomain enumeration** using public sources (DNS, certificates, archives).
- **Live host checking** with HTTP/HTTPS status, technology detection, and titles.
- **Historical URL collection** from Wayback Machine and Common Crawl archives.
- **Report generation** in two formats:
  - `report_<domain>.json` – machine‑readable data,
  - `report_<domain>.html` – visual report with tables and statistics.
- **Asynchronous execution** – parallel requests save time.
- **Automatic dependency installation** – required tools are downloaded on first run.

---

## Installation

### System Requirements
- Linux (Ubuntu/Debian recommended, works on any distribution)
- Required packages: `git`, `curl`, `wget`, `python3`, `python3-pip`, `python3-venv`, `golang-go`

### Clone the repository
git clone https://github.com/ForexxX1/Recon_tool.git
cd Recon_tool/recon_tool_1.0

### Install Python dependencies in a virtual environment:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

### (Optional) If you prefer to install Go tools manually, you can do so:
-subfinder
-assetfinder
-amass
-httpx
-gau
All binaries must be in $PATH or inside the tools/ folder.

### Run the script with a domain:
python main.py example.com
Or without arguments – you will be prompted to enter the domain interactively.

### Usage with modes
# Safe mode for Bug Bounty (10 threads, 100ms delay) – default
python main.py example.com --mode safe

# Fast mode for personal testing (50 threads, no delay)
python main.py example.com --mode fast

# Medium mode (30 threads, 50ms delay)
python main.py example.com --mode medium

### Project Structure
recon_tool/
├── main.py                 # Entry point
├── deps.json               # List of external tools and install commands
├── requirements.txt        # Python dependencies
├── core/
│   ├── installer.py        # Check and install external tools
│   ├── runner.py           # Asynchronous execution of tools
│   ├── collectors.py       # Direct API requests (crt.sh, DNSDumpster)
│   └── report.py           # Report generation (JSON, HTML)
├── templates/
│   └── report.html         # HTML report template

Configuration

All settings are in core/runner.py. You can tweak:

    Thread count – in httpx arguments (-threads).

    Request delay – in httpx via -delay.

    Timeouts – in run_command() calls for each tool.

    Data sources for gau – you can add additional providers via flags.

Example: to increase speed, set -threads 20 and remove -delay (but make sure you comply with your program's rules).
Sample Report

After execution you will get:

    report_example.com.json – all gathered data in structured JSON.

    report_example.com.html – a neat HTML report with summary, subdomain tables, and live hosts.

Open the HTML in a browser – it contains everything you need for manual analysis.
Responsibility

This tool is designed for lawful purposes only – e.g., testing your own projects or participating in Bug Bounty programs with official permission.

The author is not liable for any misuse. Always ensure you have the right to scan the target domain before running.
License

Distributed under the MIT License. You are free to use, modify, and distribute the code as long as you retain the copyright notice.
Contributing

Feel free to open issues or pull requests on GitHub.
└── tools/                  # Binaries are placed here (auto‑created)
