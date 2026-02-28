# Ready for Robots

## Overview
Ready for Robots is an intelligent lead discovery engine designed to identify companies that are ready to adopt robotics solutions in various industries, including hospitality, logistics, and service sectors. The system leverages advanced scraping techniques, natural language processing, and scoring algorithms to detect buying intent signals.

## Project Structure
The project is organized into several key directories:

- **app/**: Contains the main application code, including models, services, scrapers, and API endpoints.
- **worker/**: Contains the Celery worker and task definitions for handling background jobs.
- **frontend/**: Contains the Next.js frontend application files.
- **infra/**: Contains infrastructure-related files, including Docker and Kubernetes configurations.
- **migrations/**: Contains database migration scripts.
- **tests/**: Contains unit and integration tests for the application.
- **scripts/**: Contains utility scripts for setting up and running the application.
- **requirements.txt**: Lists the Python dependencies required for the project.
- **pyproject.toml**: Contains project metadata and dependencies for Python packaging.
- **alembic.ini**: Configuration settings for Alembic, the database migration tool.
- **.env.example**: Example environment variable configuration.

## Features
- **Lead Scoring**: Calculates scores based on automation keywords, labor pain signals, and expansion news.
- **Data Enrichment**: Enhances company and contact data by pulling additional information from external sources.
- **Scraping**: Implements various scrapers to gather data from hotel directories, job boards, news articles, and Google SERP.
- **API Endpoints**: Provides RESTful API endpoints for managing leads, companies, and scoring operations.
- **Background Processing**: Utilizes Celery for running scrapers and recalculating scores asynchronously.

## Getting Started
1. **Clone the Repository**: 
   ```
   git clone <repository-url>
   cd ready-for-robots
   ```

2. **Set Up Environment**: 
   Copy the `.env.example` to `.env` and configure your environment variables.

3. **Install Dependencies**: 
   ```
   pip install -r requirements.txt
   ```

4. **Run Database Migrations**: 
   ```
   alembic upgrade head
   ```

5. **Start the Application**: 
   ```
   uvicorn app.main:app --reload
   ```

6. **Run Background Worker**: 
   ```
   celery -A worker.celery_worker worker --loglevel=info
   ```

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.