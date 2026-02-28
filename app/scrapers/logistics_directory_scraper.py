"""
Build a scraper for logistics directories.

Goals:
- Extract company name
- Website
- Industry
- Location
- Size estimate (e.g., warehouse size)
- Labor shortage mentions

Create automation signals if:
- Warehouse size is 50k+ sq ft
- Hiring for automation roles
- Mentions of AMRs, AGVs, or robotics integrators

Store in database.
"""