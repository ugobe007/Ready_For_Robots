# ROBOT AUTOMATION USE CASES & ECONOMICS
## Intelligence Framework for Ready for Robots

**Updated: March 2026**

---

## Overview

This document outlines our enhanced scraping strategy to capture **real-world robot deployments, economics, and buying decisions** from three perspectives:

1. **Customer/Buyer** - What problems are they solving? Why now?
2. **Analyst** - What trends are emerging? Which solutions win?
3. **Investor** - What's the ROI? Where's the money flowing?

---

## Signal Types We're Tracking

### **Tier 1: Deployment Signals (High Value)**

| Signal Type | Weight | Description | Example |
|-------------|--------|-------------|---------|
| `robot_installation` | 10 | Actual robot deployed in production | "Marriott deploys Savioke robots in 50 hotels" |
| `roi_documented` | 9 | Published ROI/payback data | "18-month payback, 30% labor savings" |
| `scale_expansion` | 8 | Pilot converting to fleet | "Trial of 5 robots expands to 50 properties" |
| `pilot_success` | 8 | Successful pilot announcement | "90-day pilot exceeded expectations" |

### **Tier 2: Decision Signals (Medium-High Value)**

| Signal Type | Weight | Description | Example |
|-------------|--------|-------------|---------|
| `economics_driven` | 8 | Clear financial case stated | "Robot saves $42K annually vs. labor" |
| `vendor_selection` | 7 | Chose specific robot vendor | "Selected Universal Robots over ABB" |
| `competitive_response` | 7 | Reacting to competitor | "Hilton responds to Marriott automation" |
| `problem_solution` | 7 | Robot solving specific issue | "Addresses 40% housekeeping vacancy rate" |

---

## Query Categories

### **1. Actual Deployments (Not Exploration)**

Focus on **past tense** language indicating completed installations:

- "hotel **deployed** housekeeping robot"
- "warehouse **implemented** AMR fleet"
- "hospital **installed** disinfection robot"
- "restaurant **introduces** service robot"

**Why This Matters:**  
These companies have crossed the "exploration → execution" chasm. They're validation for similar buyers.

---

### **2. ROI & Economics**

Capture the **financial justification** driving decisions:

**Queries:**
- "robot automation ROI case study [industry]"
- "warehouse automation payback period 2026"
- "labor cost savings robot deployment"
- "service robot saves money hotel"

**What We Extract:**
- Payback period (18 months, 24 months, etc.)
- Labor cost comparison (robot vs. human FTE)
- Productivity gains (% increase in throughput)
- Quality improvements (defect reduction, uptime)

**Example Intelligence:**
```
Company: Hilton Hotels
Robot: Savioke Relay (delivery robot)
Deployment: 100 properties
Economics:
  - Robot lease: $2,500/month
  - Replaces: 0.5 FTE per property ($1,800/month)
  - Guest service improvement: 15% faster response
  - Payback: 14 months including installation
```

---

### **3. Problem → Solution Stories**

These narratives show **why** companies automate (the "push" factor):

**Problems We Track:**
- Labor shortage (can't fill positions)
- Turnover (hiring/training costs too high)
- Safety (workers comp claims, injuries)
- Consistency (quality variation with human labor)
- Scale (can't grow without automation)
- 24/7 ops (can't staff third shift)

**Example Story:**
```
Problem: Las Vegas hotel with 35% housekeeping vacancy rate
         Overtime costs $500K annually to cover open shifts
         Guest satisfaction scores dropping

Solution: Deployed 8 housekeeping robots (trash/linen transport)
          Allowed existing staff to focus on cleaning (higher value)
          
Results:  Vacancy rate still 35%, but service improved
          Overtime reduced 60% ($300K annual savings)
          Guest scores up 12 points
          Payback: 22 months
```

---

### **4. Vendor-Specific Deployments**

Track which vendors are **winning deals** in which verticals:

**Hospitality:**
- Savioke Relay (delivery)
- Makr Shakr (bartender)
- Bear Robotics (restaurant service)

**Warehouse/Logistics:**
- MiR, Fetch, OTTO, Locus (AMRs)
- GreyOrange, Geek+ (goods-to-person)

**Healthcare:**
- Diligent Robotics Moxi (hospital logistics)
- Xenex (disinfection)
- TUG (medication delivery)

**Manufacturing:**
- Universal Robots, ABB (cobots)
- FANUC, KUKA (industrial arms)

**Cleaning:**
- Brain Corp (floor scrubbers)
- SoftBank Whiz (commercial cleaning)

**Why This Matters:**  
Vendor momentum indicates product-market fit. If Savioke dominates hospitality delivery, competing vendors need different positioning.

---

### **5. Technology Trends**

Capture emerging capabilities that enable new use cases:

**Current Trends (2026):**
- **AI-powered navigation** - Robots learning optimal routes from fleet data
- **Computer vision picking** - Handling variety without pre-programming
- **Fleet orchestration** - Coordinating 100+ robots via cloud software
- **Collaborative manipulation** - Two robots cooperating on assembly
- **RaaS models** - Robotics-as-a-Service lowering upfront costs
- **5G connectivity** - Remote operation and real-time updates

**Example Intelligence:**
```
Trend: Computer vision-based picking
Impact: Robots can now handle 10,000+ SKU variety
        Previously required fixed bins/slots

Winner: Amazon robots using CV pick 40% more SKUs
Implication: Smaller warehouses can now justify automation
              (don't need standardization)
```

---

### **6. Buyer Persona Signals**

Track **who** is making automation decisions:

**Decision Makers:**
- VP Operations (operational efficiency)
- CFO (financial justification)
- COO (strategic transformation)
- Facilities Director (cleaning, maintenance)
- Supply Chain VP (logistics, warehouse)
- CTO/CIO (technology integration)

**Buyer Committees:**
- Operations + Finance + HR (headcount impact)
- Real Estate + Facilities (for hotels, offices)
- Clinical + IT (for hospitals)

**Example:**
```
"Hilton's Chief Operations Officer announces automation strategy 
 targeting 30% task reduction in housekeeping departments"

Signal: C-level commitment = strategic priority
Weight: High (executive initiatives get budget)
```

---

### **7. Competitive Pressure**

Companies automate because **rivals did**:

**Queries:**
- "competitor automates forces response"
- "automation competitive advantage hospitality"
- "rivals deploy robots market pressure"

**Example:**
```
After Marriott deployed delivery robots in 50 properties,
Hilton accelerated their pilot from 5 to 25 hotels.

Why: Guest perception that Marriott is "more modern"
      Operational efficiency gap creates cost disadvantage
```

---

### **8. Metrics & KPIs**

Capture **quantified outcomes** (the proof):

**Operational Metrics:**
- Picks per hour (warehouse: 100 → 300 with robots)
- Square feet cleaned per hour (20,000 sq ft unmanned)
- Deliveries per shift (200 room service orders)
- Uptime percentage (98.5% robot vs 85% human staffing)

**Financial Metrics:**
- Labor cost as % of revenue (40% → 28%)
- Cost per unit shipped ($4.50 → $2.80)
- Overtime expense reduction ($500K → $150K)

**Quality Metrics:**
- Defect rate (5% → 0.2%)
- Guest satisfaction (NPS 45 → 58)
- Safety incidents (12 injuries → 0)

---

## Use Case Categories

### **Hospitality Use Cases**

| Use Case | Robot Type | Leaders | Typical ROI |
|----------|-----------|---------|-------------|
| Room service delivery | Mobile delivery | Savioke, Aethon | 12-18 months |
| Housekeeping logistics | Mobile AMR | Custom builds | 18-24 months |
| Pool/grounds cleaning | Outdoor cleaner | Dolphin, Milagrow | 6-12 months |
| Front desk assistant | Social robot | SoftBank Pepper | TBD (experimental) |
| Kitchen prep | Cobot | Miso Robotics | 24-36 months |

### **Warehouse Use Cases**

| Use Case | Robot Type | Leaders | Typical ROI |
|----------|-----------|---------|-------------|
| Goods-to-person | AMR + shelving | Amazon, GreyOrange | 18-24 months |
| Pallet transport | Heavy AMR | OTTO, Seegrid | 12-18 months |
| Picking assistance | Cobot arm | RightHand, Berkshire Grey | 24-30 months |
| Inventory scanning | Autonomous drone | Corvus, Verity | 12-15 months |
| Sortation | Conveyor + vision | SICK, Cognex | 24-36 months |

### **Healthcare Use Cases**

| Use Case | Robot Type | Leaders | Typical ROI |
|----------|-----------|---------|-------------|
| Supply delivery | Mobile delivery | TUG, Diligent Moxi | 18-24 months |
| Disinfection | UV robot | Xenex, UVD | 12-18 months |
| Medication dispensing | Pharmacy robot | Omnicell, BD Rowa | 24-36 months |
| Linen transport | Mobile AMR | Aethon | 18-24 months |
| Telepresence rounds | Remote robot | InTouch Health | TBD (quality focus) |

### **Manufacturing Use Cases**

| Use Case | Robot Type | Leaders | Typical ROI |
|----------|-----------|---------|-------------|
| Assembly | Cobot | Universal Robots, ABB | 8-12 months |
| Welding | Industrial arm | FANUC, KUKA | 10-14 months |
| Material handling | AMR | MiR, Fetch | 18-24 months |
| Quality inspection | Vision system | Cognex, Keyence | 4-8 months |
| Packaging | Delta robot | ABB FlexPicker | 5-10 months |

---

## Economic Decision Frameworks

### **Customer/Buyer Perspective**

**Question:** "Should I deploy robots?"

**Decision Factors:**
1. **Labor availability** - Can I hire enough humans?
2. **Labor cost** - What does turnover + training + OT cost?
3. **Consistency** - Do I need 24/7 or perfect quality?
4. **Safety** - Are tasks dangerous/repetitive strain?
5. **Scale** - Can I grow without adding headcount?

**Break-Even Analysis:**
```
Human Cost:
  - Salary: $35K/year
  - Benefits: $10K/year
  - Turnover: $8K/year (recruiting, training)
  - Management overhead: $5K/year
  - Total: $58K/year

Robot Cost:
  - Lease: $30K/year
  - Maintenance: $5K/year
  - Electricity: $1K/year
  - Total: $36K/year

Savings: $22K/year per FTE replaced
Payback: If robot costs $40K upfront, payback = 22 months
```

---

### **Analyst Perspective**

**Question:** "Which solutions will win?"

**Analysis Framework:**
1. **Technology maturity** - Is it proven or experimental?
2. **Vendor momentum** - How many deployments?
3. **Customer satisfaction** - Do buyers renew/expand?
4. **Competitive dynamics** - Switching costs, lock-in
5. **Unit economics** - Does ROI improve at scale?

**Example Analysis:**
```
Category: Warehouse Mobile Robots

Leaders: Amazon Robotics, MiR, Fetch, Locus
Emerging: Geek+, GreyOrange, IAM Robotics

Why Leaders Win:
- Proven at scale (500+ deployments)
- Fleet management software mature
- Integration ecosystem (WMS, ERP)
- ROI data published

Emerging Risk:
- Chinese vendors (Geek+) offering 40% lower pricing
- Could disrupt via RaaS models
```

---

### **Investor Perspective**

**Question:** "Where's the TAM and growth?"

**Market Sizing:**
```
Addressable Market (Service Robots):
  - Hospitality: 50,000 properties globally
  - Warehouses: 150,000 facilities
  - Hospitals: 40,000 facilities
  - Manufacturing: 300,000 facilities

Penetration (2026):
  - Hospitality: 2% (1,000 properties)
  - Warehouses: 8% (12,000 facilities)
  - Hospitals: 3% (1,200 facilities)
  - Manufacturing: 25% (75,000 facilities)

Growth Rate:
  - Hospitality: 45% CAGR (early adopter phase)
  - Warehouses: 30% CAGR (scaling phase)
  - Hospitals: 35% CAGR (regulatory clearing)
  - Manufacturing: 15% CAGR (mature market)

Money Follows Success:
- VC funding: $8B into robotics startups (2026)
- Top areas: Warehouse automation, healthcare logistics
- Exits: 3 IPOs, 12 acquisitions (2025-2026)
```

---

## Scraper Enhancement Checklist

### ✅ **Phase 1: Query Expansion** (Now)
- [x] Add 50+ deployment-focused queries
- [x] Add vendor-specific tracking
- [x] Add ROI/economics queries

### 🔄 **Phase 2: Signal Classification** (Next)
- [ ] Tag signals by use case category
- [ ] Extract economic data (payback, savings)
- [ ] Identify decision maker role
- [ ] Track competitive moves

### 📊 **Phase 3: Intelligence Synthesis** (Future)
- [ ] Generate industry reports by vertical
- [ ] ROI benchmarking dashboard
- [ ] Vendor market share tracking
- [ ] Technology trend analysis

---

## Next Actions

1. **Run enhanced intelligence scraper** with new queries
2. **Classify existing 158 companies** by use case
3. **Extract ROI data** from signals for benchmarking
4. **Build vendor tracking** dashboard
5. **Create buyer personas** for targeted outreach

---

**Money follows success. We track the success.**
