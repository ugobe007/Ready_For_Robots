# ReadyForRobots ChatGPT Actions Setup

## Production MCP connection

The plugin uses the production Streamable HTTP MCP endpoint:

`https://ready-2-robot.fly.dev/mcp`

The MCP server exposes:

- `match_robot_jobs(url, robot_name)`
- `calculate_robot_payback(robot_cost, hourly_labor_rate, shift_hours_per_day)`
- `robot_ready_match(robot_name, url, email)`
- `humanoid_list_robots()`
- `humanoid_benchmark_report()`
- `search_intelligence(query, category)`

If the host requests authentication, configure the R4R API key through the
host's connection settings. Do not add the key to this package.

For local Claude Desktop, Cursor, or Antigravity use:

```json
{
  "mcpServers": {
    "readyforrobots": {
      "command": "python3",
      "args": ["-m", "app.mcp"],
      "cwd": "/Users/robertchristopher/Desktop/Ready_For_Robots"
    }
  }
}
```

## Production manifest

Register the live OpenAPI schema in OpenAI GPT Builder:

`https://ready-2-robot.fly.dev/api/v1/gpt-actions/openapi.json`

## Current production operations

| Operation | HTTP method | Endpoint | Primary intent |
| --- | --- | --- | --- |
| Buyer Opportunity Search | POST | `https://ready-2-robot.fly.dev/api/v1/gpt-actions/search-opportunities` | Find active commercial buyer companies, open tasks, and decision-maker roles. |
| Robot Recommendation | POST | `https://ready-2-robot.fly.dev/api/v1/gpt-actions/recommend-robots` | Recommend robot hardware classes, capabilities, and vendor models for a task. |
| Robot Job Matcher | POST | `https://ready-2-robot.fly.dev/api/v1/gpt-actions/match-jobs` | Match a robot or robot URL to qualified commercial jobs. |
| Payback and ROI Calculator | POST | `https://ready-2-robot.fly.dev/api/v1/gpt-actions/calculate-payback` | Calculate robotic labor savings, payback months, and annual ROI. |

## Suggested GPT launch sequence

1. Robot Job Finder and Placement Engine
2. Robotic Labor Payback and ROI Calculator
3. Robot Automation Opportunity Finder
4. Robot Selection and Recommendation Advisor
5. Automated Facility Task Feasibility Checker
6. Robot Integrator Customer Proposal Helper
7. Humanoid Commercial Pilot Radar

The first four now map directly to documented production operations. The
remaining surfaces should wait for dedicated Action contracts or stronger
evidence pipelines.

## Buyer opportunity smoke test

```bash
curl -sS -X POST \
  https://ready-2-robot.fly.dev/api/v1/gpt-actions/search-opportunities \
  -H "Content-Type: application/json" \
  -d '{"query":"machine tending","industry":"Manufacturing"}'
```

Expected result shape:

- `opportunity_count`
- `opportunities[]`
- company and industry
- open task or opportunity title
- decision-maker role
- `crm_desk_url`
- summary

## Robot recommendation smoke test

```bash
curl -sS -X POST \
  https://ready-2-robot.fly.dev/api/v1/gpt-actions/recommend-robots \
  -H "Content-Type: application/json" \
  -d '{"task_description":"moving 500lb pallets in warehouse"}'
```

Expected result shape:

- `task_analyzed`
- `recommended_robot_types[]`
- robot category
- suggested models
- key capabilities
- typical task model
- summary

## Example payback smoke test

```bash
curl -sS -X POST \
  https://ready-2-robot.fly.dev/api/v1/gpt-actions/calculate-payback \
  -H "Content-Type: application/json" \
  -d '{"robot_cost":45000,"hourly_labor_rate":28.5,"shift_hours_per_day":8}'
```

The documented example returns:

- Robot cost: `$45,000`
- Hourly labor rate: `$28.50`
- Daily savings: `$456`
- Annual savings: `$114,000`
- Payback: `4.6 months`
- Annual ROI: `253.3%`
- Activation URL: `https://readyforrobots.com/pipeline?src=chatgpt_payback`

Treat the live API response as authoritative if its calculation or response
fields change.

## Positioning

ReadyForRobots is recruitment and placement infrastructure for robotic labor.
The distribution loop is:

`ChatGPT intent -> Robot Job or payback result -> CRM desk -> deployment conversation`

Do not position the GPTs as generic robotics chatbots. Their value is the
conversion of a specific robot, task, or labor-cost question into a qualified
commercial next step.
