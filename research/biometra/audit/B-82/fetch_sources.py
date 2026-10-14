import argparse
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlparse


class PageText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.skip = max(0, self.skip - 1)

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def normalise(text):
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def quote_key(text):
    return re.sub(r"[^a-z0-9]+", " ", normalise(text).lower()).strip()


parser = argparse.ArgumentParser()
parser.add_argument("input")
parser.add_argument("output")
parser.add_argument("--existing", action="store_true")
args = parser.parse_args()
data = json.loads(Path(args.input).read_text())
categories = {"supplement", "medication", "recovery", "food-protocol", "exercise", "context", "lab-marker"}
entries = (
    {key: value for key, value in data.items() if key.split(":")[1] in categories and value.get("community")}
    if args.existing else data["entries"]
)
requests = {}
for entry_id, entry in entries.items():
    for protocol in entry.get("community", []):
        requests.setdefault(protocol["source"]["url"], []).append({
            "id": entry_id, "description": protocol["description"],
            "quote": protocol.get("supportingQuote", ""),
        })
    if not args.existing and not entry.get("community"):
        for attempt in entry["attempts"]:
            if urlparse(attempt["url"]).scheme == "https":
                requests.setdefault(attempt["url"], [])
            else:
                print(f"Pending correction, not a source: {entry_id}: {attempt['url']}", flush=True)

output = Path(args.output)
output.mkdir(parents=True, exist_ok=True)
results_path = output / "results.json"
cached = {entry["url"]: entry for entry in json.loads(results_path.read_text())} if results_path.exists() else {}
results = []
next_index = len(cached)
for index, (url, claims) in enumerate(requests.items()):
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError(f"Not a public HTTPS citation: {url}")
    if url in cached:
        result = cached[url]
        text = Path(result["textFile"]).read_text()
        for claim in claims:
            claim["quoteMatched"] = bool(claim["quote"]) and quote_key(claim["quote"]) in quote_key(text)
        result["claims"] = claims
        results.append(result)
        print(f"Cached HTTP {result['httpStatus']} {url}", flush=True)
        continue
    path = output / f"{next_index:03d}.html"
    response = subprocess.run([
        "curl", "--silent", "--show-error", "--location", "--max-time", "25",
        "--max-filesize", "5242880", "--proto", "=https", "--proto-redir", "=https",
        "--output", str(path), "--write-out", "%{http_code}\n%{url_effective}", url,
    ], capture_output=True, text=True)
    metadata = response.stdout.splitlines()
    text = ""
    if path.exists():
        page = PageText()
        page.feed(path.read_text(errors="replace"))
        text = normalise(" ".join(page.parts))
    text_path = output / f"{next_index:03d}.txt"
    next_index += 1
    text_path.write_text(text)
    for claim in claims:
        claim["quoteMatched"] = bool(claim["quote"]) and quote_key(claim["quote"]) in quote_key(text)
    result = {
        "url": url, "httpStatus": metadata[0] if metadata else "000",
        "finalURL": metadata[1] if len(metadata) > 1 else url,
        "exitCode": response.returncode, "error": response.stderr.strip(),
        "textFile": str(text_path), "textLength": len(text), "claims": claims,
    }
    results.append(result)
    print(f"{index:03d} HTTP {result['httpStatus']} {len(text)} chars {url}", flush=True)
    results_path.write_text(json.dumps(results, indent=2))
results_path.write_text(json.dumps(results, indent=2))
