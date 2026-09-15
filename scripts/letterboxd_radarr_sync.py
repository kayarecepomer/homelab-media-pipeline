#!/usr/bin/env python3
"""Watch a public Letterboxd list and add new films to Radarr.

See docs/letterboxd-automation.md in the repo root for how this works and
why it's built this way (Letterboxd's list RSS route no longer works, and
the site sits behind Cloudflare, so we go through FlareSolverr and scrape
the rendered page instead).
"""
import json, os, re, urllib.request, urllib.parse

CONF_PATH = os.path.expanduser(os.environ.get("LB_RADARR_CONF", "~/scripts/letterboxd-radarr.conf"))
STATE_PATH = os.path.expanduser(os.environ.get("LB_RADARR_STATE", "~/scripts/letterboxd-radarr.seen.json"))

conf = {}
with open(CONF_PATH) as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        k, _, v = line.partition("=")
        conf[k.strip()] = v.strip()

seen = set(json.load(open(STATE_PATH))) if os.path.exists(STATE_PATH) else set()

def call(url, data=None, method="GET", timeout=30):
    req = urllib.request.Request(url, data=data, method=method,
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

fs_payload = json.dumps({
    "cmd": "request.get",
    "url": conf["LIST_URL"],
    "maxTimeout": 60000,
}).encode()
fs_result = json.loads(call(conf["FLARESOLVERR_URL"], data=fs_payload, method="POST", timeout=75))
html = fs_result["solution"]["response"]

FILM_RE = re.compile(
    r'href="/film/([a-z0-9-]+)/"\s+class="frame"\s+data-original-title="([^"(]+?)\s*\((\d{4})\)\s*"'
)

for slug, title, year in FILM_RE.findall(html):
    if slug in seen:
        continue
    title, year = title.strip(), int(year)

    lookup_url = f'{conf["RADARR_URL"]}/api/v3/movie/lookup?term={urllib.parse.quote(title)}&apikey={conf["RADARR_API_KEY"]}'
    results = json.loads(call(lookup_url))
    match = next((r for r in results if r.get("year") == year), results[0] if results else None)

    if not match:
        print(f"no Radarr match: {title} ({year})")
        seen.add(slug)
        continue
    if match.get("id"):
        print(f"already in Radarr: {title} ({year})")
        seen.add(slug)
        continue

    payload = json.dumps({
        "title": match["title"], "titleSlug": match["titleSlug"],
        "tmdbId": match["tmdbId"], "year": match["year"],
        "qualityProfileId": int(conf["QUALITY_PROFILE_ID"]),
        "rootFolderPath": conf["ROOT_FOLDER"],
        "monitored": True, "addOptions": {"searchForMovie": True},
    }).encode()
    call(f'{conf["RADARR_URL"]}/api/v3/movie?apikey={conf["RADARR_API_KEY"]}', data=payload, method="POST")
    print(f"added: {match['title']} ({match['year']})")
    seen.add(slug)

json.dump(list(seen), open(STATE_PATH, "w"))
