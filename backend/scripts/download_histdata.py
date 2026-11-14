"""Download HistData.com free yearly M1 zips (does what the site's download form does).

  .\\.venv\\Scripts\\python scripts\\download_histdata.py xauusd 2019 2024
Saves to backend\\data\\histdata\\<pair>\\ (gitignored). Years 2025+ are refused (locked out-of-sample).
"""
import re
import sys
import time
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

UA = {"User-Agent": "LITTLE/0.1 (personal backtest research)"}


def main() -> int:
    pair, y0, y1 = sys.argv[1].lower(), int(sys.argv[2]), int(sys.argv[3])
    if y1 >= 2025:
        print("Refused: 2025+ is the locked out-of-sample period.")
        return 2
    out = Path(__file__).resolve().parent.parent / "data" / "histdata" / pair
    out.mkdir(parents=True, exist_ok=True)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
    for year in range(y0, y1 + 1):
        target = out / f"HISTDATA_COM_ASCII_{pair.upper()}_M1_{year}.zip"
        if target.exists() and target.stat().st_size > 100_000:
            print(year, "already there")
            continue
        page = f"https://www.histdata.com/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/{pair}/{year}"
        html = opener.open(urllib.request.Request(page, headers=UA), timeout=60).read().decode("utf-8", "replace")
        form = re.search(r'<form[^>]*id="file_down".*?</form>', html, re.S)
        if not form:
            print(year, "no download form on the page")
            continue
        fields = dict(re.findall(r'name="([^"]+)"[^>]*value="([^"]*)"', form.group(0)))
        req = urllib.request.Request("https://www.histdata.com/get.php", data=urllib.parse.urlencode(fields).encode(),
                                     headers={**UA, "Referer": page, "Content-Type": "application/x-www-form-urlencoded"})
        data = opener.open(req, timeout=300).read()
        if data[:2] != b"PK":
            print(year, "NOT a zip:", data[:120])
            continue
        target.write_bytes(data)
        print(year, f"{len(data) / 1e6:.1f} MB saved to {target}")
        time.sleep(5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
