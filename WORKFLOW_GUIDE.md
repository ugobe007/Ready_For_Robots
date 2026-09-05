# Robot Company Workflow Management

## Overview
Track next steps for each of the 200+ robotics companies in your pipeline. Never lose track of where you are in the sales process.

## Workflow Stages

1. **Research** - Initial company investigation
2. **Outreach** - First contact attempt
3. **Demo** - Product demonstration scheduled
4. **Proposal** - Partnership proposal sent
5. **Negotiation** - Terms being discussed
6. **Partnership** - Deal closed

## Workflow Fields

### workflow_stage
Current stage in sales pipeline (research → partnership)

### next_action
Specific task to complete next
- Example: "Send partnership intro email"
- Example: "Schedule technical demo for cobot line"
- Example: "Follow up on pricing proposal"

### next_action_date
Deadline for completing the next action
- Used for reminders and upcoming actions view
- Query `/api/robot-companies/workflow/upcoming?days=7` for weekly planning

### assigned_to
Team member responsible for this relationship
- Sales Team
- Technical Team
- Partnerships
- CEO

### workflow_notes
Running log of all activity (timestamped automatically)
- Each update appends to notes with timestamp
- Creates audit trail of all interactions
- Example: `[2026-03-07 10:30] CEO interested in U.S. expansion. Demo scheduled for next week.`

### workflow_history
JSON array of stage changes (automated audit trail)
```json
[
  {
    "date": "2026-03-07 10:30",
    "stage": "demo",
    "previous_stage": "outreach",
    "action": "Schedule technical demo for cobot line"
  }
]
```

### blockers
What's preventing progress?
- Example: "Waiting for pricing approval from China HQ"
- Example: "Need technical specs for integration"
- Example: null (no blockers)

## Usage

### View Workflows
Navigate to `/robot-companies` to see all companies with their current workflow status.

Table shows:
- Workflow stage (color-coded)
- Next action with date
- Edit Workflow button

### Edit Workflow
1. Click "Edit Workflow" button for any company
2. Update workflow fields:
   - Set workflow stage
   - Define next action
   - Pick next action date
   - Assign to team member
   - Add activity notes
   - Note any blockers
3. Click "Save Workflow"

All changes are logged to workflow_history automatically.

### Track Upcoming Actions
API endpoint for weekly planning:
```bash
curl http://localhost:8000/api/robot-companies/workflow/upcoming?days=7
```

Returns all companies with actions due in next 7 days, ordered by date.

## API Endpoints

### Update Workflow
```http
PUT /api/robot-companies/{company_id}/workflow
Content-Type: application/json

{
  "workflow_stage": "demo",
  "next_action": "Schedule product demo",
  "next_action_date": "2026-03-15",
  "assigned_to": "Sales Team",
  "workflow_notes": "CEO interested in AMR solutions",
  "blockers": null
}
```

Response:
```json
{
  "message": "Workflow updated",
  "company": "Unitree Robotics",
  "workflow_stage": "demo",
  "next_action": "Schedule product demo",
  "next_action_date": "2026-03-15"
}
```

### Get Upcoming Actions
```http
GET /api/robot-companies/workflow/upcoming?days=7
```

Response:
```json
{
  "upcoming_actions": [
    {
      "id": 2,
      "company_name": "ForwardX Robotics",
      "workflow_stage": "outreach",
      "next_action": "Send partnership intro email",
      "next_action_date": "2026-03-10",
      "assigned_to": "Sales Team",
      "priority_tier": "hot",
      "lead_score": 78,
      "blockers": null
    }
  ],
  "count": 1,
  "days": 7
}
```

## Example Workflows

### ForwardX Robotics (Hot Lead)
- **Stage**: Outreach
- **Next Action**: Send partnership intro email
- **Assigned To**: Sales Team
- **Notes**: Company showed interest at ProMat 2025. Need to follow up on distributor expansion plans.
- **Blockers**: None

### AUBO Robotics (Hot Lead)
- **Stage**: Demo
- **Next Action**: Schedule technical demo for cobot line
- **Assigned To**: Technical Team
- **Notes**: Initial contact made. CEO interested in U.S. expansion. Demo scheduled for next week.
- **Blockers**: None

## Best Practices

1. **Always set next_action_date** - Enables follow-up tracking
2. **Log every interaction** - Add notes after calls, emails, meetings
3. **Update stage regularly** - Keep pipeline accurate
4. **Clear blockers fast** - Track and resolve what's slowing deals
5. **Assign ownership** - Every company needs a responsible party
6. **Review upcoming actions weekly** - Use `/workflow/upcoming?days=7` endpoint

## Migration
Database migration `3b95a4c9c416_add_workflow_fields.py` adds all workflow fields to existing robot_companies table.

Run migration:
```bash
alembic upgrade head
```

## Scaling to 200+ Companies
The workflow system is designed to handle:
- 200+ companies with unique workflows
- Multiple team members managing different portfolios
- Automated reminders for upcoming actions
- Full audit trail of all relationship history
- Bulk workflow updates via API

Next: Build dashboard view filtering by workflow stage, assigned team member, and upcoming deadlines.
