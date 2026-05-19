"""
Celery Beat Schedule - Automated Scraper Jobs
==============================================
Production-grade scheduled tasks for continuous lead discovery
Similar to pythh.ai investor/startup scraping system
"""
from celery.schedules import crontab

# Source Monitoring Taxonomy from Robot Automation Signal Ontology.md.
# This keeps the polling intent close to the executable schedule.
SOURCE_MONITORING_TAXONOMY = {
    "linkedin_job_postings": {"signal_types": ["Job Title Signals", "Hiring Intent"], "frequency": "Daily"},
    "earnings_calls": {"signal_types": ["CapEx Signals", "Trigger Expressions", "Pain Words"], "frequency": "Quarterly"},
    "press_releases": {"signal_types": ["Expansion Signals", "Contract Wins", "Trigger Expressions"], "frequency": "Daily"},
    "osha_filings": {"signal_types": ["Safety Signals", "Pain Words"], "frequency": "Weekly"},
    "real_estate_permits": {"signal_types": ["Expansion/Facility Signals"], "frequency": "Weekly"},
    "sec_filings": {"signal_types": ["CapEx Signals", "Financial Signals"], "frequency": "Quarterly"},
    "industry_news": {"signal_types": ["News Triggers", "Regulatory Signals"], "frequency": "Daily"},
    "company_career_pages": {"signal_types": ["Job Title Signals", "Hiring Intent"], "frequency": "Daily"},
    "glassdoor_indeed_reviews": {"signal_types": ["Pain Words", "Labor Shortage Signals"], "frequency": "Weekly"},
    "government_contract_databases": {"signal_types": ["Contract Win Signals", "Defense Signals"], "frequency": "Weekly"},
    "linkedin_company_updates": {"signal_types": ["Expansion Signals", "Leadership Changes"], "frequency": "Daily"},
    "local_business_news": {"signal_types": ["Facility Signals", "Expansion Signals"], "frequency": "Daily"},
}

# Celery Beat Schedule - runs scrapers automatically
CELERYBEAT_SCHEDULE = {
    # ── INTELLIGENCE NEWS SCRAPER ── FREE lead discovery (runs 3x daily)
    'intelligence-scraper-morning': {
        'task': 'worker.tasks.run_intelligence_scraper_task',
        'schedule': crontab(hour=9, minute=0),  # 9am UTC (4am EST)
        # Bounded run (~20 shuffled queries) + light enrich — same defaults as task / cron quick mode
        'kwargs': {
            'max_articles': 15,
            'max_queries': 20,
            'enrich': True,
            'enrich_limit': 20,
        },
    },
    'intelligence-scraper-afternoon': {
        'task': 'worker.tasks.run_intelligence_scraper_task',
        'schedule': crontab(hour=15, minute=0),  # 3pm UTC (10am EST)
        'kwargs': {
            'max_articles': 15,
            'max_queries': 20,
            'enrich': True,
            'enrich_limit': 20,
        },
    },
    'intelligence-scraper-evening': {
        'task': 'worker.tasks.run_intelligence_scraper_task',
        'schedule': crontab(hour=21, minute=0),  # 9pm UTC (4pm EST)
        'kwargs': {
            'max_articles': 15,
            'max_queries': 20,
            'enrich': True,
            'enrich_limit': 20,
        },
    },
    
    # ── NEWS SCRAPERS ── Industry news + local business news (daily / intraday)
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
    
    # ── JOB BOARD SCRAPERS ── LinkedIn-like job/career-page signals (daily / intraday)
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
    
    # ── RSS FEEDS ── Press releases, trade publications, regulatory/news triggers
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
    
    # ── SERP SCRAPER ── Local business news + facility/permit-like expansion searches
    'serp-expansion-signals': {
        'task': 'worker.tasks.run_serp_scraper_task',
        'schedule': crontab(hour='0,8,16', minute=45),
    },
    
    # ── RFP MARKETPLACE ── Government contracts / procurement signals
    'rfp-marketplace-daily': {
        'task': 'worker.tasks.run_rfp_marketplace_scraper_task',
        'schedule': crontab(hour=5, minute=0),
    },
    
    # ── LINKEDIN SCRAPER ── disabled: task body is a stub (TODO: LinkedIn API creds)
    # 'linkedin-company-scraper': {
    #     'task': 'worker.tasks.run_linkedin_scraper_task',
    #     'schedule': crontab(hour='9,17', minute=0),
    #     'kwargs': {'max_companies': 50},
    # },
    
    # ── SCORING ENGINE ── Re-score all companies daily at 6am UTC
    'rescore-all-companies': {
        'task': 'worker.tasks.rescore_all_companies_task',
        'schedule': crontab(hour=6, minute=0),
    },
    # ── COMPANY → NEWS ── Search news for each company (XYZ → news on XYZ)
    'company-news-morning': {
        'task': 'worker.tasks.run_company_news_task',
        'schedule': crontab(hour=8, minute=30),
        'kwargs': {'limit': 80},
    },
    'company-news-afternoon': {
        'task': 'worker.tasks.run_company_news_task',
        'schedule': crontab(hour=16, minute=30),
        'kwargs': {'limit': 80},
    },
    # ── LEAD RESEARCH AGENT ── Profile updates + in-app notifications.
    # Task itself is gated by LEAD_RESEARCH_AGENT_ENABLED=1 until reviewed.
    'lead-research-daily': {
        'task': 'worker.tasks.research_active_leads_task',
        'schedule': crontab(hour=10, minute=15),
        'kwargs': {'limit': 50, 'dry_run': False, 'lookback_days': 30},
    },
    # ── ENRICH EXISTING ── Add signals to companies with fewest (daily 7am UTC)
    'enrich-existing-companies': {
        'task': 'worker.tasks.run_enrich_companies_task',
        'schedule': crontab(hour=7, minute=0),
        'kwargs': {'limit': 80},
    },
    
    # ── RECTIFY + CRM ENRICH ── Nightly quality sweep (rectification + CRM extraction)
    # Also triggered automatically after run_enrich_companies_task.
    'rectify-crm-nightly': {
        'task': 'worker.tasks.rectify_and_enrich_crm_task',
        'schedule': crontab(hour=2, minute=30),   # 2:30am UTC daily
        'kwargs': {'limit': 150, 'hours_since_scraped': 48},
    },

    # ── CLEANUP ── Remove old/junk leads weekly
    'cleanup-junk-leads': {
        'task': 'worker.tasks.cleanup_junk_leads_task',
        'schedule': crontab(day_of_week=1, hour=2, minute=0),  # Monday 2am
    },
    
    # ── HEARTBEAT ── Proves scheduler is alive (every 2 min). Prevents "stuck" appearance.
    'scheduler-heartbeat': {
        'task': 'worker.tasks.scheduler_heartbeat_task',
        'schedule': 120.0,  # Every 2 minutes (seconds)
    },
    # ── HEALTH CHECK ── Monitor scraper health every hour
    'scraper-health-check': {
        'task': 'worker.tasks.scraper_health_check_task',
        'schedule': crontab(minute=0),  # Every hour
    },
    
    # ── DAILY REPORT ── Performance metrics (actual vs projected)
    'daily-scraper-report': {
        'task': 'worker.tasks.daily_scraper_report_task',
        'schedule': crontab(hour=8, minute=0),  # Daily at 8am UTC
    },
    # ── NEWSLETTER ── Generate daily edition for posting (every 24h at 9am UTC)
    'newsletter-daily': {
        'task': 'worker.tasks.generate_newsletter_edition_task',
        'schedule': crontab(hour=9, minute=0),
        'kwargs': {'limit': 8},
    },
    # ── DAILY OPPORTUNITY ANALYTICS ── Automation types, robots needed, ROI, tasks (9:15am UTC)
    'daily-analytics-report': {
        'task': 'worker.tasks.daily_analytics_report_task',
        'schedule': crontab(hour=9, minute=15),
        'kwargs': {'days': 1},
    },
}

# Timezone
CELERY_TIMEZONE = 'UTC'
