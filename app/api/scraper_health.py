"""
Scraper Health API
==================
Exposes watchdog status, circuit breaker controls, and run history.

Endpoints:
  GET  /scraper-health              — full health report
  GET  /scraper-health/circuits     — only open circuit breakers
  POST /scraper-health/reset/{url}  — manually reset a circuit breaker
  POST /scraper-health/reset-all    — reset all circuit breakers
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from urllib.parse import unquote
from app.scrapers.scraper_watchdog import get_watchdog

router = APIRouter()


@router.get("/scraper-health")
def scraper_health():
    """Full watchdog health report — run history, circuit breakers, active runs."""
    watchdog = get_watchdog()
    data = watchdog.status()
    # Summarise for quick dashboard widget
    total_urls    = len(data["url_health"])
    open_circuits = len(data["circuit_open_urls"])
    recent        = data["recent_runs"][-1] if data["recent_runs"] else None
    data["summary"] = {
        "total_urls_tracked":   total_urls,
        "open_circuits":        open_circuits,
        "healthy_urls":         total_urls - open_circuits,
        "last_run_status":      recent["status"] if recent else "no runs yet",
        "last_run_scraper":     recent["scraper_name"] if recent else None,
        "last_run_finished_at": recent["finished_at"] if recent else None,
    }
    return data


@router.get("/scraper-health/circuits")
def open_circuits():
    """List URLs currently blocked by open circuit breakers."""
    watchdog = get_watchdog()
    status = watchdog.status()
    return {
        "open_circuits": status["circuit_open_urls"],
        "count": len(status["circuit_open_urls"]),
    }


@router.post("/scraper-health/reset/{url:path}")
def reset_circuit(url: str):
    """
    Manually reset the circuit breaker for a specific URL.
    URL must be URL-encoded in the path, e.g.:
      POST /scraper-health/reset/https%3A%2F%2Fexample.com
    """
    decoded_url = unquote(url)
    watchdog = get_watchdog()
    found = watchdog.reset_circuit(decoded_url)
    if found:
        return {"status": "reset", "url": decoded_url}
    return JSONResponse(status_code=404,
                        content={"error": f"URL not found in watchdog: {decoded_url}"})


@router.post("/scraper-health/reset-all")
def reset_all_circuits():
    """Reset ALL open circuit breakers. Use after fixing a broken scraper."""
    watchdog = get_watchdog()
    watchdog.reset_all_circuits()
    return {"status": "all circuits reset"}
