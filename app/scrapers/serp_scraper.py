"""
Build a scraper for Google SERP queries.

Goals:
- Extract company expansion signals from search results.
- Use search queries like:
  - "expanding warehouse" + city
  - "opening new hotel" + year
  - "seeking automation partner"

For each result, extract:
- Company name
- URL
- Snippet text
- Signal type (expansion, automation, etc.)

Create automation signals based on:
- Keywords indicating expansion or automation needs.

Store results in the database.
"""