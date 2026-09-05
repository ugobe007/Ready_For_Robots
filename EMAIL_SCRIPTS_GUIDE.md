# Email Introduction Scripts

## Overview
Automated, personalized email templates for robot company outreach. Generate professional introduction emails tailored to each company's profile and workflow stage.

## Features

### 6 Email Templates

1. **Introduction Email** (`intro`)
   - Initial outreach to new companies
   - Personalizes based on U.S. presence status
   - Highlights value proposition
   - **Use when**: First contact, cold outreach

2. **Demo Request Email** (`demo`)
   - Request product demonstration
   - Proposes technical review agenda
   - Schedules meeting time
   - **Use when**: Company shows initial interest

3. **Partnership Proposal Email** (`proposal`)
   - Formal partnership offer after demo
   - 3-phase market entry plan
   - ROI projections and timeline
   - **Use when**: After successful demo, ready to commit

4. **Follow-up Email** (`followup`)
   - Re-engage non-responsive leads
   - 3 variations based on days since last contact
   - Value-added approach (not pushy)
   - **Use when**: No response after 3-7 days

5. **Trade Show Invitation** (`trade_show`)
   - Invite to Automate, ProMat, MODEX, etc.
   - Schedule booth meetings
   - Offer integrator introductions
   - **Use when**: Upcoming trade show, company attending

6. **Hot Lead Priority Email** (`hot_lead`)
   - High-urgency outreach for score >= 85
   - Time-sensitive opportunities
   - Direct integrator introductions
   - **Use when**: Hot lead with immediate opportunity

### Personalization

Each email automatically personalizes based on:
- **Company name** - Addressed directly
- **Robot type** - AMR, cobot, industrial, humanoid, etc.
- **Target market** - Warehouse, manufacturing, hospitality, etc.
- **U.S. presence** - None (market entry), Distributor (expansion), Office (growth)
- **Lead score** - Priority level and urgency
- **Unique selling points** - Technology differentiators

## Usage

### UI - Email Button

1. Navigate to `/robot-companies`
2. Click **📧 Email** button for any company
3. Modal opens with email templates
4. Select template type (Intro, Demo, Proposal, etc.)
5. Preview personalized email
6. Click **Copy to Clipboard**
7. Paste into your email client

### API - Generate Email

```bash
GET /api/robot-companies/{company_id}/email?template_type=intro
```

**Template Types:**
- `intro` - Initial introduction
- `demo` - Demo request
- `proposal` - Partnership proposal
- `followup` - Follow-up for non-responsive
- `trade_show` - Trade show meeting
- `hot_lead` - High-priority hot lead

**Response:**
```json
{
  "company_id": 2,
  "company_name": "Unitree Robotics",
  "template_type": "intro",
  "email": {
    "subject": "U.S. Market Entry Partnership - Unitree Robotics",
    "body": "Hi [First Name],\n\nI came across Unitree Robotics and was impressed by your humanoid solutions for automation...",
    "suggested_followup_days": 3
  }
}
```

### Log Email Sent

Track outreach activity:

```bash
POST /api/robot-companies/{company_id}/email/log
Content-Type: application/json

{
  "template_type": "intro",
  "subject": "U.S. Market Entry Partnership - Unitree Robotics"
}
```

Automatically:
- Updates `last_contact_date`
- Logs to `workflow_notes`
- Changes `outreach_status` from `not_contacted` → `contacted`

## Email Templates

### 1. Introduction Email

**Subject:** U.S. Market Entry Partnership - [Company Name]

**When to use:**
- First contact with new lead
- Cold outreach
- No prior relationship

**Personalization:**
- Adjusts angle based on U.S. presence (none, distributor, office)
- Highlights target market opportunity
- Mentions robot type expertise

**Follow-up:** 3 days

### 2. Demo Request Email

**Subject:** Demo Request: Technical Review of [Company Name] [ROBOT_TYPE]

**When to use:**
- Company responded to intro
- Showing interest in partnership
- Ready for technical discussion

**Key points:**
- 60-minute agenda proposed
- Technical + business discussion
- Flexible scheduling

**Follow-up:** 5 days

### 3. Partnership Proposal Email

**Subject:** Partnership Proposal: U.S. Market Entry Plan for [Company Name]

**When to use:**
- After successful demo
- Strong mutual fit confirmed
- Ready to formalize partnership

**Includes:**
- 3-phase market entry plan
- Timeline and milestones
- Investment structure
- Attachment mention (PDF proposal)

**Follow-up:** 7 days

### 4. Follow-up Email (3 variations)

**Friendly Reminder (≤7 days):**
- Light touch
- Quick recap
- Low pressure

**Value-Added (8-14 days):**
- Share market intelligence
- Trade show opportunities
- Industry trends

**Last Attempt (>14 days):**
- Polite exit
- Open door for future
- No pressure

**Follow-up:** 14 days (or none for last attempt)

### 5. Trade Show Invitation

**Subject:** Meet at [Trade Show] [Year] - U.S. Market Entry Discussion

**When to use:**
- Upcoming trade show (Automate, ProMat, MODEX)
- Company planning to attend
- Want to schedule meeting

**Offers:**
- Booth meeting
- Integrator introductions
- Private reception invite

**Follow-up:** 5 days

### 6. Hot Lead Priority Email

**Subject:** 🔥 U.S. Market Opportunity for [Company Name] - High Priority

**When to use:**
- Lead score >= 85
- Time-sensitive opportunity
- Active integrators searching NOW

**Urgency:**
- 48-hour response window
- Direct calendar link
- Phone number included
- Top 5% mention

**Follow-up:** 2 days

## Workflow Integration

### Automatic Template Selection

Set `workflow_stage` and emails auto-select:

- `research` → Intro email
- `outreach` → Intro email
- `demo` → Demo request email
- `proposal` → Partnership proposal email
- `negotiation` → Partnership proposal email

### Email Tracking

All sent emails logged to:
- **workflow_notes** - Timestamped activity log
- **last_contact_date** - Last outreach timestamp
- **outreach_status** - Pipeline stage (not_contacted → contacted → responded → etc.)

## Best Practices

### 1. Personalize Further
- Replace `[First Name]` with actual contact
- Add specific details from research
- Reference recent news/funding if relevant

### 2. Timing
- **Best days**: Tuesday-Thursday
- **Best time**: 9-11am EST (for China contacts, this is evening)
- **Avoid**: Mondays, Fridays, holidays

### 3. Follow-up Cadence
- **Day 1**: Send intro email
- **Day 3**: First follow-up if no response
- **Day 7**: Second follow-up with value-add
- **Day 14**: Final follow-up or close

### 4. A/B Testing
- Test subject lines (with/without company name)
- Test email length (short vs. detailed)
- Test CTA (call vs. meeting vs. reply)

### 5. Track Metrics
- **Open rate**: Subject line effectiveness
- **Response rate**: Email content quality
- **Meeting rate**: Value proposition fit

## Examples

### Example 1: Chinese Cobot Company, No U.S. Presence

**Company:** AUBO Robotics  
**Type:** cobot  
**Market:** manufacturing  
**Presence:** distributor  
**Score:** 85

**Generated Email:**
```
Subject: U.S. Market Entry Partnership - AUBO Robotics

Hi [First Name],

I came across AUBO Robotics and was impressed by your cobot solutions 
for manufacturing. I noticed you're expanding your U.S. distributor 
network, and I think there's a strong fit for collaboration.

We help established robotics companies scale their U.S. presence 
through strategic partnerships with regional distributors and system 
integrators.

What We Offer:
• Access to 500+ vetted U.S. system integrators and distributors
• Market entry strategy and localization support
• Trade show coordination (Automate, ProMat, MODEX)
• Lead generation and customer introductions

Why This Matters Now:
The U.S. manufacturing automation market is growing 23% YoY, with 
strong demand for proven cobot technology. Companies that establish 
partnerships in Q1 2026 are capturing the early-mover advantage.

Would you be open to a 20-minute call next week to explore how we 
can accelerate your U.S. growth?

Best regards,
[Your Name]
Ready For Robots
www.readyforrobots.com

P.S. We recently helped [Similar Company] expand from 2 to 15 U.S. 
distributors in 6 months. Happy to share that playbook.
```

### Example 2: Hot Lead - Humanoid Robot Company

**Company:** Unitree Robotics  
**Type:** humanoid  
**Score:** 95  
**USPs:** CES 2025 showcase, advanced AI, competitive pricing

**Generated Email:**
```
Subject: 🔥 U.S. Market Opportunity for Unitree Robotics - High Priority

Hi [First Name],

I've been tracking Unitree Robotics and I'm reaching out because 
you're uniquely positioned for rapid U.S. market success.

Why You Stand Out:
• CES 2025 showcase
• Advanced AI
• Competitive pricing

The Opportunity:
We have 3 U.S. system integrators actively searching for humanoid 
solutions RIGHT NOW. They're:
• Currently evaluating competitive products
• Ready to commit to partnerships in Q1 2026
• Looking for proven technology with strong support

Fast Track Process:
If you're interested, I can arrange introductions THIS WEEK. 
Here's the timeline:
• Day 1-2: Share your tech overview with integrators
• Day 3-5: Schedule demo calls
• Week 2: Partnership discussions if there's mutual fit

This is time-sensitive - they're making decisions in the next 
2-3 weeks.

Can we connect for 15 minutes in the next 48 hours?

Calendar Link: [Insert scheduling link]
Direct Line: [Phone number]

Best,
[Your Name]
Ready For Robots

P.S. Score: 95/100 - You're in the top 5% of companies we track 
for U.S. market readiness.
```

## Technical Details

### File Structure
```
app/services/email_templates.py - Template generation logic
app/api/robot_companies.py - API endpoints
frontend/nextjs/pages/robot-companies.js - UI components
```

### Dependencies
- None (pure Python, no external libraries)
- Works with existing robot_companies database

### Future Enhancements
- [ ] Email sending integration (SendGrid/Mailgun)
- [ ] Open/click tracking
- [ ] A/B test variants
- [ ] Multi-language support (Chinese translations)
- [ ] Calendar invite attachments
- [ ] Email sequence automation (drip campaigns)
- [ ] Response templates for replies

## Quick Reference

| Template Type | Use Case | Follow-up Days | Urgency |
|--------------|----------|----------------|---------|
| intro | First contact | 3 | Low |
| demo | Request demo | 5 | Medium |
| proposal | Formalize partnership | 7 | Medium |
| followup | Re-engage | 14 | Low |
| trade_show | Event meeting | 5 | Medium |
| hot_lead | Time-sensitive | 2 | **HIGH** |

---

**Pro Tip:** Combine email templates with workflow management. After sending an email:
1. Log send with `/email/log` endpoint
2. Update `next_action` to "Follow up on intro email"
3. Set `next_action_date` to +3 days
4. Track response in `workflow_notes`
