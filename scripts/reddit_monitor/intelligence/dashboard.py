from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .profiles import load_profile, save_profile


INDEX_HTML = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Reddit Intelligence</title><style>body{font:15px system-ui;max-width:1180px;margin:auto;padding:24px;background:#f6f7fb;color:#172033}button,select,input,textarea{padding:8px;border:1px solid #cbd3e1;border-radius:7px}button{cursor:pointer;background:#172033;color:white}textarea{width:100%;min-height:340px;font:12px ui-monospace}.card{background:white;border:1px solid #dce1eb;border-radius:10px;padding:14px;margin:8px 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}small{color:#657083}.pill{background:#eaf1ff;padding:3px 8px;border-radius:12px}.tabs button{margin-right:6px}.hidden{display:none}.danger{color:#9b1c1c}.evidence{border-left:3px solid #8aa4d6;padding-left:9px}</style></head>
<body><h1>Reddit Intelligence</h1><p id="mode"></p><div class="grid" id="summary"></div>
<div class="tabs"><button onclick="tab('opportunities')">Opportunities</button><button onclick="tab('alerts')">Urgent alerts</button><button onclick="tab('digest')">Weekly digest</button><button onclick="tab('briefs')">Content briefs</button><button onclick="tab('setup')">Setup</button></div>
<section id="opportunities"><h2>Opportunity bank</h2><input id="filter" placeholder="Filter questions, groups, or subreddit" oninput="renderOpps()"><div id="opps"></div></section>
<section id="alerts" class="hidden"><h2>Urgent alert previews</h2><div id="alertsBody"></div></section>
<section id="digest" class="hidden"><h2>Weekly digest preview</h2><pre class="card" id="digestBody"></pre></section>
<section id="briefs" class="hidden"><h2>Content brief previews</h2><div id="briefsBody"></div></section>
<section id="setup" class="hidden"><h2>Setup and activation</h2><div class="card"><b>Safety state</b><p id="activation"></p><small>Reddit posting, messaging, voting, and account automation are not available. Sheet and email adapters fail closed until explicitly installed and activated.</small></div><h3>Profile contract</h3><textarea id="profile"></textarea><p><button onclick="saveProfile()">Validate and save profile</button> <span id="saveState"></span></p></section>
<script>let state={};async function j(u,o){let r=await fetch(u,o);let x=await r.json();if(!r.ok)throw Error(x.error);return x}function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}function tab(id){document.querySelectorAll('section').forEach(x=>x.classList.add('hidden'));document.getElementById(id).classList.remove('hidden')}function cards(items){return items.map(x=>`<div class=card><b>${esc(x.title||x.question||x.proposed_title)}</b><p>${esc(x.summary||x.search_intent||x.reason||'')}</p></div>`).join('')||'<div class=card>No preview items yet.</div>'}function renderOpps(){let q=filter.value.toLowerCase();let rows=(state.opportunities||[]).filter(x=>JSON.stringify(x).toLowerCase().includes(q));opps.innerHTML=rows.map(x=>`<div class=card><b>${esc(x.title)}</b> <span class=pill>${esc(x.status)}</span><br><small>r/${esc(x.subreddit)} · intent ${x.commercial_intent} · content ${x.content_value} · risk ${x.reputation_risk}</small><p>${esc(x.summary)}</p><p class=evidence>“${esc(x.evidence_quote)}”</p><select onchange="setStatus('${encodeURIComponent(x.id)}',this.value)">${state.profile.statuses.map(v=>`<option ${v==x.status?'selected':''}>${esc(v)}</option>`).join('')}</select> <a href="${esc(x.url)}" target=_blank rel=noopener>Source</a></div>`).join('')||'<div class=card>No matching opportunities.</div>'}async function load(){state=await j('/api/state');mode.textContent=`Mode: ${state.activation.mode} · External effects: ${state.activation.external_effects.length?'ON':'OFF'}`;activation.textContent=JSON.stringify(state.activation);summary.innerHTML=`<div class=card>Opportunities<br><b>${state.opportunities.length}</b></div><div class=card>Urgent previews<br><b>${state.urgent_alerts.length}</b></div><div class=card>Content briefs<br><b>${state.content_briefs.length}</b></div>`;profile.value=JSON.stringify(state.profile,null,2);alertsBody.innerHTML=cards(state.urgent_alerts);digestBody.textContent=JSON.stringify(state.weekly_digest,null,2);briefsBody.innerHTML=cards(state.content_briefs);renderOpps()}async function setStatus(id,status){await j('/api/opportunities/'+id,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({status})});load()}async function saveProfile(){try{await j('/api/profile',{method:'PUT',headers:{'Content-Type':'application/json'},body:profile.value});saveState.textContent='Saved';await load()}catch(e){saveState.textContent=e.message;saveState.className='danger'}}load()</script></body></html>"""


def read_json(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


class DashboardStore:
    def __init__(self, profile_path: str | Path, data_dir: str | Path):
        self.profile_path, self.data_dir = Path(profile_path), Path(data_dir)

    def state(self) -> dict:
        profile = load_profile(self.profile_path)
        manifest = read_json(self.data_dir / "run-manifest.json", {"mode": "dry_run", "external_effects": []})
        return {"profile": profile, "activation": {"mode": manifest.get("mode", "dry_run"),
                "external_effects": manifest.get("external_effects", [])},
                "opportunities": read_json(self.data_dir / "opportunities.json", []),
                "urgent_alerts": read_json(self.data_dir / "urgent-alerts.preview.json", []),
                "weekly_digest": read_json(self.data_dir / "weekly-digest.preview.json", {}),
                "content_briefs": read_json(self.data_dir / "content-briefs.preview.json", [])}

    def update_status(self, item_id: str, status: str) -> dict:
        profile = load_profile(self.profile_path)
        if status not in profile["statuses"]:
            raise ValueError("status is not allowed by the profile contract")
        path = self.data_dir / "opportunities.json"
        rows = read_json(path, [])
        found = next((row for row in rows if row["id"] == item_id), None)
        if not found:
            raise KeyError(item_id)
        found["status"] = status
        path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
        with (self.data_dir / "opportunities.jsonl").open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        return found

    def replace_profile(self, profile: dict) -> dict:
        return save_profile(self.profile_path, profile)


def make_handler(store: DashboardStore):
    class Handler(BaseHTTPRequestHandler):
        def _json(self, value, status=HTTPStatus.OK):
            body = json.dumps(value, ensure_ascii=False).encode()
            self.send_response(status); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

        def _body(self):
            return json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))) or b"{}")

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/":
                body = INDEX_HTML.encode(); self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
            elif path == "/api/state": self._json(store.state())
            elif path == "/api/profile": self._json(store.state()["profile"])
            else: self._json({"error": "not found"}, 404)

        def do_PATCH(self):
            path = urlparse(self.path).path
            try:
                if path.startswith("/api/opportunities/"):
                    self._json(store.update_status(path.rsplit("/", 1)[-1], self._body().get("status", "")))
                else: self._json({"error": "not found"}, 404)
            except (ValueError, KeyError) as exc: self._json({"error": str(exc)}, 400)

        def do_PUT(self):
            try:
                if urlparse(self.path).path == "/api/profile": self._json(store.replace_profile(self._body()))
                else: self._json({"error": "not found"}, 404)
            except ValueError as exc: self._json({"error": str(exc)}, 400)

        def log_message(self, format, *args):
            return
    return Handler


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Self-contained Reddit Intelligence dashboard")
    parser.add_argument("--profile", required=True); parser.add_argument("--data-dir", required=True)
    parser.add_argument("--host", default="127.0.0.1"); parser.add_argument("--port", type=int, default=8788)
    args = parser.parse_args(argv)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(DashboardStore(args.profile, args.data_dir)))
    print(f"Reddit Intelligence dashboard: http://{args.host}:{args.port}")
    server.serve_forever(); return 0


if __name__ == "__main__":
    raise SystemExit(main())
