"""Guard: Vercel Vite builds must inline the public Supabase project."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FLY = (ROOT / "fly.toml").read_text()
WORKFLOW = (ROOT / ".github/workflows/deploy-frontend.yml").read_text()
VITE = (ROOT / "readyforrobots-new/vite.config.ts").read_text()
SMOKE = (ROOT / "scripts/vercel_production_smoke.py").read_text()

SUPABASE_HOST = "lmoyydlhlgdyqbxkmkuz.supabase.co"


def test_fly_and_vercel_workflow_share_public_supabase_project():
    url = re.search(r'VITE_PUBLIC_SUPABASE_URL\s*=\s*"([^"]+)"', FLY)
    key = re.search(r'VITE_PUBLIC_SUPABASE_ANON_KEY\s*=\s*"([^"]+)"', FLY)
    assert url and SUPABASE_HOST in url.group(1)
    assert key and len(key.group(1)) > 20
    assert "VITE_PUBLIC_SUPABASE_URL" in WORKFLOW
    assert url.group(1) in WORKFLOW
    assert key.group(1) in WORKFLOW
    assert "VITE_PUBLIC_API_URL" in WORKFLOW


def test_vite_production_build_requires_supabase_env():
    assert "requirePublicSupabaseEnv" in VITE
    assert "supabase.co" in VITE


def test_production_smoke_requires_supabase_host_in_js():
    assert SUPABASE_HOST in SMOKE
    assert "REQUIRED_JS_SUBSTRINGS" in SMOKE
