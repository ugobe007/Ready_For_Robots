module.exports = {
  apps: [
    {
      name: 'seed-leads-v2',
      script: 'python3',
      args: 'scripts/seed_leads_v2.py --commit',
      cwd: '/Users/robertchristopher/Desktop/Ready_For_Robots',
      interpreter: 'none',
      autorestart: false,
      watch: false,
      env: {
        DATABASE_URL: process.env.DATABASE_URL || 'sqlite:///./ready_for_robots.db'
      }
    },
    {
      name: 'seed-leads-v3',
      script: 'python3',
      args: 'scripts/seed_leads_v3.py --commit',
      cwd: '/Users/robertchristopher/Desktop/Ready_For_Robots',
      interpreter: 'none',
      autorestart: false,
      watch: false,
      env: {
        DATABASE_URL: process.env.DATABASE_URL || 'sqlite:///./ready_for_robots.db'
      }
    },
    {
      name: 'job-board-scraper',
      script: 'python3',
      args: 'app/scrapers/job_board_scraper.py',
      cwd: '/Users/robertchristopher/Desktop/Ready_For_Robots',
      interpreter: 'none',
      autorestart: true,
      watch: false,
      cron_restart: '0 */6 * * *', // Every 6 hours
      env: {
        DATABASE_URL: process.env.DATABASE_URL || 'sqlite:///./ready_for_robots.db'
      }
    },
    {
      name: 'news-scraper',
      script: 'python3',
      args: 'app/scrapers/news_scraper.py',
      cwd: '/Users/robertchristopher/Desktop/Ready_For_Robots',
      interpreter: 'none',
      autorestart: true,
      watch: false,
      cron_restart: '30 */4 * * *', // Every 4 hours at :30
      env: {
        DATABASE_URL: process.env.DATABASE_URL || 'sqlite:///./ready_for_robots.db'
      }
    },
    {
      name: 'logistics-scraper',
      script: 'python3',
      args: 'app/scrapers/logistics_directory_scraper.py',
      cwd: '/Users/robertchristopher/Desktop/Ready_For_Robots',
      interpreter: 'none',
      autorestart: true,
      watch: false,
      cron_restart: '0 0 * * *', // Daily at midnight
      env: {
        DATABASE_URL: process.env.DATABASE_URL || 'sqlite:///./ready_for_robots.db'
      }
    },
    {
      name: 'hotel-directory-scraper',
      script: 'python3',
      args: 'app/scrapers/hotel_directory_scraper.py',
      cwd: '/Users/robertchristopher/Desktop/Ready_For_Robots',
      interpreter: 'none',
      autorestart: true,
      watch: false,
      cron_restart: '0 2 * * *', // Daily at 2 AM
      env: {
        DATABASE_URL: process.env.DATABASE_URL || 'sqlite:///./ready_for_robots.db'
      }
    }
  ]
};
