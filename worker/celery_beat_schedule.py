"""
Celery Beat Schedule - Automated Scraper Jobs
==============================================
Production-grade scheduled tasks for continuous lead discovery
Similar to pythh.ai investor/startup scraping system
"""
from celery.schedules import crontab

# Celery Beat Schedule - runs scrapers automatically
CELERYBEAT_SCHEDULE = {
    # ── NEWS SCRAPERS ── Run every 2 hours during business hours
    'news-scraper-morning': {
        'task': 'worker.tasks.run_news_scraper_task',
        'schedule': crontab(hour='6,8,10', minute=0),  # 6am, 8am, 10am UTC
        'kwargs': {'industry': None},  # All industries
    },
    'news-scraper-afternoon': {
        'task': 'worker.tasks.run_news_scraper_task',
        'schedule': crontab(hour='12,14,16', minute=0),  # 12pm, 2pm, 4pm UTC
        'kwargs': {'industry': None},
    },
    
    # ── MANUFACTURING NEWS ── Dedicated manufacturing signal searches
    'manufacturing-news': {
        'task': 'worker.tasks.run_manufacturing_news_task',
        'schedule': crontab(hour='7,15', minute=30),  # 7:30am, 3:30pm UTC
    },
    
    # ── JOB BOARD SCRAPERS ── Run every 6 hours
    'job-board-hospitality': {
        'task': 'worker.tasks.run_job_scraper_task',
        'schedule': crontab(hour='*/6', minute=15),
        'kwargs': {'industry': 'hospitality'},
    },
    'job-board-logistics': {
        'task': 'worker.tasks.run_job_scraper_task',
        'schedule': crontab(hour='1,7,13,19', minute=15),
        'kwargs': {'industry': 'logistics'},
    },
    'job-board-healthcare': {
        'task': 'worker.tasks.run_job_scraper_task',
        'schedule': crontab(hour='2,8,14,20', minute=15),
        'kwargs': {'industry': 'healthcare'},
    },
    
    # ── RSS FEEDS ── Run every 4 hours
    'rss-feeds-all': {
        'task': 'worker.tasks.run_rss_scraper_task',
        'schedule': crontab(hour='*/4', minute=30),
    },
    
    # ── HOTEL DIRECTORY ── Run daily at 3am UTC
    'hotel-directory-daily': {
        'task': 'worker.tasks.run_hotel_scraper_task',
        'schedule': crontab(hour=3, minute=0),
    },
    
    # ── LOGISTICS DIRECTORY ── Run daily at 4am UTC
    'logistics-directory-daily': {
        'task': 'worker.tasks.run_logistics_scraper_task',
        'schedule': crontab(hour=4, minute=0),
    },
    
    # ── SERP SCRAPER ── Run every 8 hours for expansion/growth signals
    'serp-expansion-signals': {
        'task': 'worker.tasks.run_serp_scraper_task',
        'schedule': crontab(hour='0,8,16', minute=45),
    },
    
    # ── RFP MARKETPLACE ── Run daily at 5am UTC
    'rfp-marketplace-daily': {
        'task': 'worker.tasks.run_rfp_scraper_task',
        'schedule': crontab(hour=5, minute=0),
    },
    
    # ── LINKEDIN SCRAPER ── Run twice daily (requires auth)
    'linkedin-company-scraper': {
        'task': 'worker.tasks.run_linkedin_scraper_task',
        'schedule': crontab(hour='9,17', minute=0),  # 9am, 5pm UTC
        'kwargs': {'max_companies': 50},
    },
    
    # ── SCORING ENGINE ── Re-score all companies daily at 6am UTC
    'rescore-all-companies': {
        'task': 'worker.tasks.rescore_all_companies_task',
        'schedule': crontab(hour=6, minute=0),
    },
    
    # ── CLEANUP ── Remove old/junk leads weekly
    'cleanup-junk-leads': {
        'task': 'worker.tasks.cleanup_junk_leads_task',
        'schedule': crontab(day_of_week=1, hour=2, minute=0),  # Monday 2am
    },
    
    # ── HEALTH CHECK ── Monitor scraper health every hour
    'scraper-health-check': {
        'task': 'worker.tasks.scraper_health_check_task',
        'schedule': crontab(minute=0),  # Every hour
    },
}

# Timezone
CELERY_TIMEZONE = 'UTC'
