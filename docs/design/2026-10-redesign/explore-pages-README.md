# Explore pages (2026-10-16)

Add to docs/design/2026-10-redesign/ (design/, static/, shots/). Same tokens and shared components as the first six pages.

| Design | Replaces | Data |
|---|---|---|
| Explore | new /explore | static cards + latest brief items |
| RobotIndex | /robot-ready, /robots | GET /api/humanoid/robots (+ classified rfr_robot_products when a read endpoint exists). Filter chips by class, search, row -> detail panel, "Find buyers for X". Scores only for humanoids; hide when missing. |
| Brief | /newsletter, /intelligence, /market-insights | GET /api/newsletter/edition; POST /api/newsletter/subscribe. Items grouped by signal tier, each with source link and "robots that fit". |
| ROI | /roi-calculator, /roi, /benchmark | POST /api/vendor-design/compute-roi (RoiComputeIn). Real inputs are typed fields; the design uses steppers only for the mockup. Show `issues` from the API in the "A buyer will question this" box. |
| Reports | /reports/benchmarking[/:industry] | One template for all nine industries; figures from the database at build time; hide any figure that can't be computed. |

Values in [brackets] and rows badged SAMPLE / EXAMPLE are placeholders. Never ship a hardcoded number (copy rule 3).
