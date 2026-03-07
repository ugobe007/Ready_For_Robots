# Robot Company Lead Generation System

## Overview
A comprehensive B2B lead generation database for tracking 200+ global robotics companies entering the U.S. market. Focus: Chinese robot manufacturers seeking U.S. distribution partners.

---

## Business Model

**Value Proposition**: Connect Chinese robotics companies with U.S. distributors, system integrators, and automation sales networks.

**Target Market**: Chinese robotics manufacturers who need:
- U.S. market entry support
- Distribution network partnerships
- System integrator relationships
- Trade show connections
- Sales channel development

**Opportunity Size**: 
- 200+ global robotics companies
- Primary focus: Chinese companies (100+ targets)
- Categories: Industrial robots, cobots, AMRs, humanoids, service robots, vision systems

---

## Database Schema

### Core Tracking Fields

#### Company Identity
- `company_name` - Full company name
- `country` - Headquarters country
- `headquarters_city` - HQ location
- `founded_year` - Year established

#### Robot Classification
- `robot_type` - industrial | AMR | cobot | humanoid | service | vision
- `target_market` - manufacturing | warehouse | service | healthcare | hospitality
- `production_scale` - low | medium | high | mass_production

#### U.S. Market Intelligence
- `us_presence` - none | distributor | office
- `us_office_location` - City if U.S. office exists
- `distributor_needed` - yes | maybe | no
- `distributor_urgency` - high | medium | low
- `system_integrator_network` - JSON array of current partners

#### Market Entry Timing
- `market_entry_wave` - wave_1 | wave_2 | wave_3
  - **Wave 1** (2020-2024): Already established U.S. presence
  - **Wave 2** (2024-2026): Rapid expansion phase ⭐ HOTTEST
  - **Wave 3** (2025-2027): Emerging next-gen AI robotics
- `entry_priority` - immediate | 6_months | 12_months | monitoring

#### Trade Show Intelligence
- `trade_shows` - JSON array [Automate, ProMat, CES, Hannover]
- `last_trade_show` - Most recent trade show attendance
- `next_trade_show` - Upcoming trade show plans

#### Funding & Scale
- `funding_stage` - startup | series_a | series_b | series_c | series_d | public | private
- `funding_amount` - Latest funding round size
- `investors` - JSON array of key investors
- `revenue_estimate` - Estimated annual revenue
- `employee_count` - Company size
- `customer_count_global` - Global customer base
- `customer_count_us` - U.S. customers (if any)

#### Contact Information
- `website` - Company website
- `contact_email` - General contact
- `sales_contact` - Sales team contact
- `partnerships_contact` - Partnership contact
- `linkedin_url` - LinkedIn company page

#### Lead Scoring & Pipeline
- `lead_score` - 0-100 numerical score
- `match_score` - 0-100 fit with Ready For Robots value prop
- `priority_tier` - hot | warm | cold
  - **hot**: score ≥ 85
  - **warm**: score 70-84
  - **cold**: score < 70

#### Partnership Tracking
- `partnership_stage` - exploring | active | established
- `partnership_opportunity` - Why they need Ready For Robots
- `outreach_status` - not_contacted | contacted | responded | meeting_scheduled | partnership
- `first_contact_date` - When we first reached out
- `last_contact_date` - Most recent interaction
- `next_follow_up_date` - Scheduled follow-up
- `outreach_notes` - Sales notes and context

---

## Initial Seed Data (20 Companies)

### Wave 1: Already in U.S. (2020-2024) - 9 companies
1. **Geek+** (Score: 65) - Beijing warehouse AMRs, Atlanta office
2. **ForwardX Robotics** (78) - Beijing AMRs, has distributors
3. **AUBO Robotics** (85) - Beijing cobots, HIGH urgency for distribution
4. **JAKA Robotics** (88) - Shanghai cobots, aggressive U.S. expansion
5. **Dobot Robotics** (70) - Shenzhen cobots/education
6. **Pudu Robotics** (82) - Shenzhen restaurant robots
7. **Keenon Robotics** (76) - Shanghai service robots
8. **Flexiv** (90) - Beijing adaptive robots, San Jose office
9. **Mech-Mind Robotics** (84) - Beijing robot vision

### Wave 2: Rapid Expansion (2024-2026) - 7 companies ⭐ HOTTEST
1. **Unitree Robotics** (95) ★★★ TOP PRIORITY
   - Hangzhou robot dogs + humanoids
   - Just showcased at CES 2025
   - NO U.S. presence yet
   - HIGH urgency for distribution
   
2. **Deep Robotics** (87) - Hangzhou inspection robots
3. **HaiPick Systems** (83) - Shenzhen warehouse picking
4. **Quicktron Robotics** (75) - Shanghai warehouse AMRs
5. **Han's Robot** (80) - Shenzhen cobots
6. **SEER Robotics** (72) - Shanghai AMR software
7. **Gaussian Robotics** (68) - Beijing cleaning robots

### Wave 3: Emerging AI Humanoids (2025-2027) - 4 companies
1. **AgiBot** (92) ★★ - Shanghai humanoids for manufacturing
2. **EngineAI** (89) ★★ - Beijing AI-powered humanoids
3. **Leju Robotics** (75) - Shenzhen humanoids
4. **Zhiyuan Robotics** (70) - Beijing next-gen humanoids

---

## API Endpoints

### Base URL: `/api/robot-companies`

#### Get All Companies (with filters)
```
GET /api/robot-companies/
Query params:
- country: China, US, EU, Korea, Japan
- robot_type: industrial, AMR, cobot, humanoid, service, vision
- us_presence: office, distributor, none
- priority_tier: hot, warm, cold
- market_entry_wave: wave_1, wave_2, wave_3
- distributor_needed: yes, maybe, no
- min_score: minimum lead score (0-100)
- search: company name search
```

#### Get Hot Leads
```
GET /api/robot-companies/hot-leads
Returns companies with priority_tier='hot' and score ≥ 80
```

#### Get Chinese Companies
```
GET /api/robot-companies/chinese-companies?us_presence=none
Filter by U.S. presence: none (needs distribution), distributor, office
```

#### Get Market Entry Waves
```
GET /api/robot-companies/market-entry-waves
Returns companies grouped by wave_1, wave_2, wave_3
```

#### Get Companies Needing Distribution
```
GET /api/robot-companies/needs-distribution
Returns companies where distributor_needed='yes'
```

#### Get Companies by Robot Type
```
GET /api/robot-companies/by-robot-type
Returns companies grouped by robot type
```

#### Get Database Stats
```
GET /api/robot-companies/stats
Returns:
- total_companies
- chinese_companies
- needs_distribution
- hot_leads
- no_us_presence
```

#### Get Single Company
```
GET /api/robot-companies/{id}
```

#### Update Outreach Status
```
PUT /api/robot-companies/{id}/outreach
Body: { status, notes }
Status: not_contacted, contacted, responded, meeting_scheduled, partnership
```

#### Create New Company
```
POST /api/robot-companies/
Body: company data object
```

#### Update Company
```
PUT /api/robot-companies/{id}
Body: updated company data
```

---

## Lead Prioritization System

### Scoring Factors (0-100 scale)

1. **Market Entry Timing** (40 points)
   - Wave 2 companies: +20 points (actively expanding NOW)
   - Wave 1 companies: +10 points (established, may need new partners)
   - Wave 3 companies: +15 points (early mover advantage)

2. **Distributor Urgency** (25 points)
   - HIGH urgency: +25 points
   - MEDIUM urgency: +15 points
   - LOW urgency: +5 points

3. **Trade Show Presence** (15 points)
   - Attending U.S. trade shows: +15 points
   - Planning to attend: +10 points

4. **Funding Stage** (10 points)
   - Series C+/Public: +10 points
   - Series B: +7 points
   - Series A: +5 points

5. **Robot Type (Market Fit)** (10 points)
   - Humanoid: +10 points (fastest growing)
   - Cobot: +9 points (high demand)
   - AMR: +8 points (warehouse boom)
   - Industrial: +7 points
   - Service: +6 points
   - Vision: +5 points

---

## Frontend UI

### Robot Companies Dashboard
**Page**: `/robot-companies`

**Features**:
- Stats dashboard (total companies, Chinese companies, hot leads, needs distribution, no U.S. presence)
- Filter views:
  - All Companies
  - 🔥 Hot Leads (score ≥ 80)
  - 🇨🇳 Chinese (No U.S. Presence)
  - 🤝 Needs Distribution
  - ⭐ Wave 2 (2024-2026 Expansion)
- Search by company name
- Sortable table with:
  - Lead score (color-coded: green ≥85, orange 70-84, gray <70)
  - Company name
  - Robot type
  - Country
  - U.S. presence status
  - Distributor urgency
  - Market entry wave
  - Outreach status
- Color-coded priority indicators
- Real-time filtering and search

---

## Database Files

### Model
**File**: `app/models/robot_company.py`
- SQLAlchemy ORM model
- 40+ tracking fields
- Indexes on: company_name, country, robot_type, us_presence

### Seeding Script
**File**: `scripts/seed_robot_companies.py`
- Seeds initial 20 companies
- Organized by market entry waves
- Console output shows top priorities

### API Router
**File**: `app/api/robot_companies.py`
- 11 endpoint handlers
- Comprehensive filtering
- Stats and analytics
- CRUD operations

### Migration
**File**: `migrations/versions/62c6bf204268_add_robot_companies_table_for_lead_.py`
- Alembic migration for robot_companies table
- Run with: `alembic upgrade head`

---

## Usage

### 1. Create Database Tables
```bash
cd /Users/robertchristopher/Desktop/Ready_For_Robots
/Users/robertchristopher/Desktop/Ready_For_Robots/.venv/bin/python -m alembic upgrade head
```

### 2. Seed Initial Companies
```bash
/Users/robertchristopher/Desktop/Ready_For_Robots/.venv/bin/python scripts/seed_robot_companies.py
```

### 3. Test Database
```bash
/Users/robertchristopher/Desktop/Ready_For_Robots/.venv/bin/python scripts/test_robot_api.py
```

### 4. Start API Server
```bash
/Users/robertchristopher/Desktop/Ready_For_Robots/.venv/bin/uvicorn app.main:app --reload --port 8000
```

### 5. View UI
```bash
cd frontend/nextjs
npm run dev
# Visit: http://localhost:3000/robot-companies
```

---

## Top Priority Leads

### Immediate Outreach (Score ≥ 90)

1. **Unitree Robotics** (95) ★★★
   - **Why**: Robot dogs + humanoids, just showed CES 2025
   - **Opportunity**: Ground floor with explosive growth company
   - **Action**: Immediate outreach, offer U.S. distribution matchmaking

2. **AgiBot** (92) ★★
   - **Why**: Humanoid robots for manufacturing, early mover
   - **Opportunity**: Be first U.S. partner in humanoid revolution
   - **Action**: Schedule intro call, discuss distribution strategy

3. **Flexiv** (90) ★★
   - **Why**: AI adaptive robots, already has San Jose office
   - **Opportunity**: Expand beyond current network, premium tech
   - **Action**: Offer specialized integrator partnerships

4. **EngineAI** (89) ★★
   - **Why**: AI-powered humanoids, ground floor opportunity
   - **Opportunity**: Early-stage partnership potential
   - **Action**: Monitor funding, engage when Series A closes

---

## Next Steps to Reach 200+ Companies

### Expansion Plan

1. **Wave 1 Expansion** (Target: 40 companies)
   - Add more established Chinese companies
   - European robotics companies (ABB, KUKA, Universal Robots)
   - Japanese leaders (Fanuc, Yaskawa, Kawasaki)
   - Korean innovators (Doosan, Hyundai Robotics)

2. **Wave 2 Expansion** (Target: 50 companies)
   - Fast-growing Chinese cobots
   - Warehouse automation leaders (GreyOrange, Locus, Exotec)
   - Service robot companies (Bear Robotics, SoftBank Robotics)

3. **Wave 3 Expansion** (Target: 40 companies)
   - Emerging AI robotics startups
   - Next-gen humanoid companies
   - Vision/AI software platforms

4. **Specialized Categories** (Target: 70 companies)
   - **Industrial Arms**: ~30 companies
   - **Logistics/Warehouse**: ~30 companies
   - **Service Robots**: ~20 companies
   - **Vision Systems**: ~20 companies

### Data Sources
- Crunchbase (funding + company data)
- RBR50 (Robotics Business Review top 50)
- Trade show exhibitor lists (Automate, ProMat, CES, Hannover Messe)
- LinkedIn company pages
- Robotics industry reports
- Venture capital portfolios

---

## Success Metrics

### Lead Generation KPIs
- Total companies in database: Target 200+
- Hot leads (score ≥ 85): Target 40+
- Companies needing distribution: Target 100+
- Outreach response rate: Target 30%+
- Meeting conversion rate: Target 15%+
- Partnership conversion rate: Target 5%+

### Market Coverage
- Chinese companies: 100+ (primary focus)
- U.S. companies: 30+
- European companies: 40+
- Japanese companies: 15+
- Korean companies: 10+
- Other regions: 5+

---

## Business Value

**Problem**: Hundreds of Chinese robotics companies want U.S. market entry but lack distribution networks.

**Solution**: Ready For Robots becomes "The Robotics Market Entry Platform" - connecting manufacturers with distributors/integrators.

**Revenue Opportunities**:
1. Partnership matchmaking fees
2. Trade show coordination services
3. Market entry consulting
4. Distributor network access
5. Lead generation data subscriptions

**Competitive Advantage**: First-mover in Chinese robotics → U.S. system integrator matchmaking niche.

---

## Files Created

### Backend
- ✅ `app/models/robot_company.py` - Database model
- ✅ `app/api/robot_companies.py` - API endpoints
- ✅ `scripts/seed_robot_companies.py` - Data seeding
- ✅ `scripts/test_robot_api.py` - Database testing
- ✅ `migrations/versions/62c6bf204268_*.py` - Alembic migration

### Frontend
- ✅ `frontend/nextjs/pages/robot-companies.js` - UI dashboard

### Documentation
- ✅ `ROBOT_LEAD_GENERATION.md` - This file

---

## Status

✅ Database model complete (40+ fields)
✅ Seeding script complete (20 initial companies)
✅ API endpoints complete (11 routes)
✅ Migration created and run
✅ Frontend UI complete
✅ Documentation complete

🔄 Ready to expand to 200+ companies
🔄 Ready to integrate with existing lead intelligence system
🔄 Ready to add advanced lead scoring automation

---

**Created**: 2026-03-07
**System**: Ready For Robots Lead Generation Platform
**Focus**: Chinese Robotics Companies → U.S. Market Entry
