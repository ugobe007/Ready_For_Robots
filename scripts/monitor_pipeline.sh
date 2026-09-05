#!/bin/bash
# Monitor pipeline performance - check daily lead generation

echo "🤖 Ready for Robots - Pipeline Monitor"
echo "========================================"
echo ""

# Check scraper status
echo "📊 Scraper Status:"
curl -s https://ready-2-robot.fly.dev/api/scraper/status | python3 -m json.tool
echo ""

# Get daily stats
echo "📈 Daily Statistics (Last 7 Days):"
curl -s "https://ready-2-robot.fly.dev/api/scraper/stats/daily?days=7" | python3 -m json.tool
echo ""

echo "✅ Monitoring complete"
echo ""
echo "To manually trigger all scrapers:"
echo "  curl -X POST https://ready-2-robot.fly.dev/api/scraper/run-all"
echo ""
echo "To trigger specific scraper:"
echo "  curl -X POST https://ready-2-robot.fly.dev/api/scraper/run/job_boards"
echo "  curl -X POST https://ready-2-robot.fly.dev/api/scraper/run/hotels"
echo "  curl -X POST https://ready-2-robot.fly.dev/api/scraper/run/news"
echo "  curl -X POST https://ready-2-robot.fly.dev/api/scraper/run/serp"
echo "  curl -X POST https://ready-2-robot.fly.dev/api/scraper/run/logistics"
