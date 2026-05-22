#!/usr/bin/env python3
"""
Kai Marketing OS — One-Click Netlify Deployer

This script automates the deployment of the workspace dashboard to Netlify.
It runs the build compiler, packages the assets in-memory, and uploads them
directly to Netlify via the REST API.

No external packages required (uses built-in urllib).
"""

import os
import sys
import json
import re
import zipfile
import io
import urllib.request
import urllib.error
from pathlib import Path

# Resolve paths
SCRIPT_DIR = Path(__file__).parent.resolve()
ROOT_DIR = SCRIPT_DIR.parent
WORKSPACE_DIR = ROOT_DIR / "workspace"
CONFIG_PATH = ROOT_DIR / "config.yaml"
DASHBOARD_HTML = WORKSPACE_DIR / "dashboard.html"
SPEC_JSON = WORKSPACE_DIR / "agent_ui_spec.json"

def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        # Fallback simple parser for basic yaml structure if PyYAML is not installed
        # (though PyYAML is a dependency of the repo, this adds robustness)
        data = {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                current_section = None
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if ":" in line:
                        parts = line.split(":", 1)
                        key = parts[0].strip()
                        val = parts[1].strip().strip('"').strip("'")
                        if not val and line.endswith(":"):
                            current_section = key
                            data[current_section] = {}
                        elif current_section:
                            data[current_section][key] = val
                        else:
                            data[key] = val
        except Exception:
            pass
        return data

def update_config_yaml(token: str = None, site_id: str = None, site_url: str = None):
    """Updates config.yaml with Netlify values preserving all comments and structure."""
    if not CONFIG_PATH.exists():
        # Create a simple config.yaml if it doesn't exist
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            f.write("# Netlify deployment configuration\nnetlify:\n  token: \"\"\n  site_id: \"\"\n  site_url: \"\"\n")
            
    content = CONFIG_PATH.read_text(encoding="utf-8")
    
    # Ensure netlify block exists
    if "netlify:" not in content:
        content += "\n# Netlify one-click deployment parameters\nnetlify:\n  token: \"\"\n  site_id: \"\"\n  site_url: \"\"\n"
        
    lines = content.splitlines()
    new_lines = []
    in_netlify = False
    
    updated_token = False
    updated_site_id = False
    updated_site_url = False
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("netlify:"):
            in_netlify = True
            new_lines.append(line)
            continue
            
        if in_netlify:
            # Check indentation to verify we are still inside netlify block
            if line and not line.startswith(" ") and not line.startswith("\t") and not stripped.startswith("#"):
                in_netlify = False
            else:
                if stripped.startswith("token:") and token is not None:
                    line = re.sub(r'token:\s*.*', f'token: "{token}"', line)
                    updated_token = True
                elif stripped.startswith("site_id:") and site_id is not None:
                    line = re.sub(r'site_id:\s*.*', f'site_id: "{site_id}"', line)
                    updated_site_id = True
                elif stripped.startswith("site_url:") and site_url is not None:
                    line = re.sub(r'site_url:\s*.*', f'site_url: "{site_url}"', line)
                    updated_site_url = True
                    
        new_lines.append(line)
        
    # Fallback append if not replaced inside the block
    final_content = "\n".join(new_lines) + "\n"
    CONFIG_PATH.write_text(final_content, encoding="utf-8")

def netlify_request(url: str, token: str, data: bytes = None, method: str = "GET", content_type: str = "application/json") -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Kai-CMO-Harness-Deployer"
    }
    if content_type:
        headers["Content-Type"] = content_type
        
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode("utf-8")
        try:
            error_json = json.loads(error_msg)
            message = error_json.get("message", error_msg)
        except Exception:
            message = error_msg
        raise Exception(f"Netlify API Error ({e.code}): {message}")
    except Exception as e:
        raise Exception(f"Connection Error: {e}")

def main():
    print("===================================================")
    print("  Kai Marketing OS - One-Click Dashboard Deployer  ")
    print("===================================================")
    
    # 1. Load config and check token
    config = load_yaml(CONFIG_PATH)
    netlify_config = config.get("netlify", {})
    
    token = os.environ.get("NETLIFY_AUTH_TOKEN") or os.environ.get("NETLIFY_TOKEN") or netlify_config.get("token")
    site_id = netlify_config.get("site_id")
    
    if not token:
        print("\nTo deploy your dashboard in one click, you need a Netlify Personal Access Token (PAT).")
        print("How to get a free token:")
        print("  1. Log in to https://app.netlify.com (sign up is free and takes 1 minute).")
        print("  2. Go to User Settings -> Applications -> Personal access tokens.")
        print("  3. Click 'Generate new token' and copy the token value.")
        print("-" * 50)
        try:
            token = input("Enter your Netlify Access Token: ").strip()
        except KeyboardInterrupt:
            print("\nDeployment cancelled.")
            sys.exit(1)
            
        if not token:
            print("Error: Netlify token is required to deploy.")
            sys.exit(1)
            
        # Save token to config.yaml
        update_config_yaml(token=token)
        print("✓ Token saved to config.yaml")

    # 2. Compile dashboard
    print("\n[1/3] Compiling workspace state dashboard...")
    try:
        import subprocess
        subprocess.run([sys.executable, str(SCRIPT_DIR / "build_dashboard.py")], check=True)
    except Exception as e:
        print(f"Error compiling dashboard: {e}")
        sys.exit(1)
        
    if not DASHBOARD_HTML.exists() or not SPEC_JSON.exists():
        print("Error: Compiled files not found in workspace.")
        sys.exit(1)
        
    # 3. Create site if it doesn't exist
    if not site_id:
        print("\n[2/3] Creating a new Netlify site container...")
        owner_name = config.get("owner", {}).get("name", "Operator")
        # Try to suggest a nice site name based on owner
        clean_owner = re.sub(r'[^a-zA-Z0-9-]', '', owner_name.lower().replace(" ", "-"))
        site_name_suggestion = f"kai-dashboard-{clean_owner}"
        
        try:
            # Let's request the site name. If it fails, Netlify will auto-assign a random name.
            print(f"Attempting to claim site name: {site_name_suggestion}.netlify.app")
            site_payload = json.dumps({"name": site_name_suggestion}).encode("utf-8")
            site_data = netlify_request("https://api.netlify.com/api/v1/sites", token, data=site_payload, method="POST")
        except Exception as e:
            # Fallback: create site with auto-assigned name
            print("Name already taken or unavailable. Creating site with a generated name...")
            site_payload = json.dumps({}).encode("utf-8")
            try:
                site_data = netlify_request("https://api.netlify.com/api/v1/sites", token, data=site_payload, method="POST")
            except Exception as ex:
                print(f"Error creating Netlify site: {ex}")
                sys.exit(1)
                
        site_id = site_data.get("id")
        site_url = site_data.get("ssl_url") or site_data.get("url")
        update_config_yaml(site_id=site_id, site_url=site_url)
        print(f"✓ Site created successfully!")
        print(f"  Site ID:  {site_id}")
        print(f"  Site URL: {site_url}")
    else:
        print(f"\n[2/3] Using existing Netlify site ID: {site_id}")

    # 4. Zip files in-memory
    print("\n[3/3] Zipping and deploying to Netlify...")
    dashboard_html = DASHBOARD_HTML.read_text(encoding="utf-8")
    json_state = SPEC_JSON.read_text(encoding="utf-8")
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        zip_file.writestr("index.html", dashboard_html)
        zip_file.writestr("agent_ui_spec.json", json_state)
    zip_data = zip_buffer.getvalue()
    
    # 5. Upload Deploy
    deploy_url = f"https://api.netlify.com/api/v1/sites/{site_id}/deploys"
    try:
        deploy_data = netlify_request(
            deploy_url, 
            token, 
            data=zip_data, 
            method="POST", 
            content_type="application/zip"
        )
        live_url = deploy_data.get("ssl_url") or deploy_data.get("url")
        admin_url = f"https://app.netlify.com/sites/{deploy_data.get('name')}"
        
        # Save latest URL
        update_config_yaml(site_url=live_url)
        
        print("\n" + "=" * 55)
        print("🎉 DEPLOYMENT SUCCESSFUL!")
        print("=" * 55)
        print(f"🚀 Live Dashboard:  {live_url}")
        print(f"⚙️ Netlify Admin:   {admin_url}")
        print("=" * 55)
        print("\nYou can now open this URL from your mobile phone or share it with clients!")
        print("To deploy future updates, just run this script again.")
        
    except Exception as e:
        print(f"\nDeployment upload failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
