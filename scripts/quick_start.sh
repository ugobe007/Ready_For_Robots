#!/bin/bash
# Quick start guide for pipeline management

echo "🚀 Ready for Robots - Pipeline Quick Start"
echo "=========================================="
echo ""

echo "📋 Common Commands:"
echo ""
echo "1. Check pipeline status:"
echo "   ./scripts/monitor_pipeline.sh"
echo ""
echo "2. Trigger all scrapers now:"
echo "   curl -X POST https://ready-2-robot.fly.dev/api/scraper/run-all"
echo ""
echo "3. View live logs:"
echo "   flyctl logs"
echo ""
echo "4. Check machine status:"
echo "   flyctl status"
echo ""
echo "5. SSH into machine:"
echo "   flyctl ssh console"
echo ""
echo "6. Deploy changes:"
echo "   flyctl deploy --remote-only"
echo ""
echo "7. Scale machines (if needed):"
echo "   flyctl scale count app=3"
echo "   flyctl scale memory 2048"
echo ""

echo "📊 Current Setup:"
echo "  • 122 scrape targets configured"
echo "  • Target: 100-200 leads/day"
echo "  • Scrapers run automatically 24/7"
echo "  • News feeds: every 4 hours"
echo "  • Job boards: every 12 hours"
echo "  • SERP & logistics: daily at 6am UTC"
echo ""

echo "🔗 Useful Links:"
echo "  • Dashboard: https://fly.io/apps/ready-2-robot/monitoring"
echo "  • App: https://ready-2-robot.fly.dev"
echo "  • API Docs: https://ready-2-robot.fly.dev/api/docs"
echo "  • Pipeline Docs: PIPELINE.md"
echo ""

read -p "Run pipeline status check now? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]
then
    ./scripts/monitor_pipeline.sh
fi
