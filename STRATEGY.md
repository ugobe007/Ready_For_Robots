# Ready for Robots — Corporate Strategy
**Confidential | March 2026**

---

## Executive Summary

Ready for Robots is building the full-stack robotics company for the service economy — combining a six-robot hardware portfolio (Dex, ADAM, Titan, Scorpion, Matradee, DUST-E), a foundational AI layer (VLA-based motion models), and a data network that compounds in value as robots are deployed at scale. The company already serves a growing roster of Fortune 500 customers and partners across technology, hospitality, logistics, and manufacturing — and is positioned to dramatically expand that footprint as humanoid robots shift from experimental to operational across enterprise environments.

The strategy centers on four simultaneous bets: **foundational model ownership**, **capability expansion via strategic M&A** (including a targeted logistics robot acquisition), **revenue acceleration through vertical sales and partnerships**, and **humanoid platform leadership** — capturing the outsized economic opportunity that emerges as Dex and the VLA layer make general-purpose physical labor economically viable at scale.

---

## 1. Product Portfolio

| Robot | Category | Primary Markets | Key Differentiator |
|-------|----------|-----------------|--------------------|
| **Dex** | Humanoid | Logistics, Manufacturing, Hospitality | VLA-driven dexterous manipulation; general-purpose physical AI platform |
| **ADAM** | Autonomous Mobile Robot | Warehousing, Fulfillment, Facilities | High-payload AMR; enterprise fleet management; WMS integration |
| **Titan** | Heavy-Duty AMR | Logistics, Industrial, Facilities | Large-format goods movement; outdoor-capable; high-cycle environments |
| **Scorpion** | Industrial Arm / Inspection | Automation, Manufacturing, Inspection | AI-native programming; vision-guided precision; no teach-pendant required |
| **Matradee** | Service Delivery Robot | Hospitality, Food Service, Parcel Delivery | Proven F&B delivery; hotel-native PMS integrations; compact form factor |
| **DUST-E** | Autonomous Cleaning Robot | Hospitality, Facilities, Retail, Healthcare | Continuous-operation floor care; UV-C disinfection option; labor cost replacement |

**Near-term hardware priorities:** Dex anchors the foundational model investment — humanoid robots require the broadest motion library and create the most durable AI moat. Titan and ADAM together address the immediate, high-volume logistics opportunity. DUST-E is the fastest path to recurring RaaS revenue in hospitality and facilities. Matradee continues to drive enterprise hospitality relationships that open the door for Dex and ADAM upsells.

---

## 2. Foundational AI Layer — The Core Bet

### 2.1 Why VLA Models Are the Defining Investment

Vision-Language-Action (VLA) models — models that observe the world visually, interpret natural-language instructions, and generate physical robot actions — are becoming the foundational layer of robotics in the same way large language models became the foundation of software AI. Companies that own or license proprietary VLA weights trained on task-specific manipulation data will have:

- **A retraining moat:** Each deployment generates proprietary data that makes the model better, creating a flywheel competitors cannot replicate by buying hardware alone.
- **Cross-robot generalization:** A well-trained VLA model can be fine-tuned from Dex to ADAM to Scorpion — one training investment amortized across the whole portfolio.
- **A licensing revenue stream:** Model weights and APIs can be sold to OEM partners or robot companies without manufacturing capabilities.

### 2.2 Technical Priorities

| Priority | Capability | Why It Matters |
|----------|-----------|----------------|
| P0 | **Dexterous manipulation** — grasping, pouring, sorting | Core to Dex and hospitality use cases |
| P0 | **Locomotion in dynamic scenes** — walking, obstacle avoidance | Matradee, ADAM, Dex in live environments |
| P1 | **Multi-modal grounding** — VLA + depth + force/torque | Precision tasks: medical, food prep, parcel handling |
| P1 | **Generalizable pick-and-place** from novel objects | Logistics/fulfillment |
| P2 | **Human-robot handoff** — co-working with staff safely | Hospitality, healthcare |

### 2.3 Data Strategy

The VLA model is only as good as the data used to train it. Ready for Robots must treat data collection as a first-class product initiative:

- **Teleoperation programs** — deploy Dex in controlled settings with human operators to generate high-quality demonstration data from day one
- **Simulated pre-training** — use NVIDIA Isaac Sim / Cosmos to generate synthetic data before physical collection begins
- **Deployed fleet data** — every live Matradee, ADAM, Titan, DUST-E, and Scorpion deployment should be instrumented to passively collect perception, navigation, and state data; this is the training signal that keeps the VLA model ahead of competitors
- **Cross-partner data sharing agreements** — structured with Ologic, Reflex, and DYNA to pool demonstrations while protecting competitive fine-tuning data

---

## 3. M&A and Investment Strategy

### 3.1 Priority Acquisition / Investment Targets

#### Reflex Robotics
- **Why:** Reflex has demonstrated real-world dexterous manipulation in service environments with advanced learning-from-demonstration pipelines. Their robot capability and vision models directly accelerate Dex's roadmap.
- **Strategic value:** Acqui-hire of ML team + integration of their VLA training stack + potential hardware cross-licensing
- **Model:** Majority acquisition preferred; minority stake + deep commercial agreement acceptable if valuation is prohibitive

#### DYNA
- **Why:** DYNA's vision learning models and robot control capabilities address the same gaps in Ready for Robots' stack. Joint model training on combined data would dramatically compress the roadmap.
- **Strategic value:** Their data and weights, not just their team — ensure IP assignment is central to any deal structure
- **Model:** Strategic investment (15–25%) with board seat and co-development agreement as a stepping-stone to full acquisition

#### Priority Logistics Robot Acquisition Target
- **Why:** The logistics market (3PL, fulfillment, distribution) represents the single largest near-term deployment opportunity for ADAM and Titan but requires deep WMS integrations, fleet orchestration software, and existing customer relationships that take years to build organically. An acquisition of a logistics-focused AMR or automation company immediately provides all three.
- **Target profile:** US-based; $20M–$150M valuation; existing contracts with 3PLs, retailers, or e-commerce fulfillment operators; proven AMR fleet software or WMS plug-in; team with operational logistics expertise
- **Candidate categories to evaluate:** Autonomous pallet/case-handling AMR companies, multi-robot orchestration software firms, last-mile fulfillment automation startups with enterprise contracts, autonomous forklift or tugger companies with proven reliability records
- **Strategic value:** Acquired customer base + fleet software becomes the distribution channel for ADAM, Titan, and eventually Dex in logistics environments
- **Model:** Full acquisition preferred; structured earn-out on contract retention acceptable

### 3.2 M&A Evaluation Criteria

When evaluating future targets, score on:

| Criterion | Weight | What to Look For |
|-----------|--------|-----------------|
| Proprietary training data / demos | 30% | >10K task demonstrations, real-world diversity |
| Model architecture / novel techniques | 25% | VLA, diffusion policy, learned world models |
| Team quality | 20% | PhD/industry robotics + ML overlap |
| Hardware capability or IP | 15% | Gripper designs, compact actuators, proprioceptive sensing |
| Revenue / customers | 10% | Existing enterprise contracts reduce integration risk |

### 3.3 Additional Watch List

| Company | Category | Interest |
|---------|----------|----------|
| **Physical Intelligence (π)** | VLA foundational models | Licensing or structured partnership before acquisition window closes |
| **Apptronik** | Humanoid | Hardware platform compatibility with Dex |
| **Viam** | Robot software / SDK | Could replace or augment internal stack |
| **Covariant** | Warehouse manipulation AI | Deep logistics-specific training data |
| **Neura Robotics** | Humanoid + cognitive layer | European market access + sensor fusion IP |
| **Vecna Robotics** | Logistics AMR + orchestration | Existing 3PL contracts + fleet software fits ADAM/Titan |
| **Righthand Robotics** | Piece-picking arms for fulfillment | Proven logistics customer base; VLA-compatible manipulation platform |
| **GreyOrange** | AI-driven warehouse AMR | Enterprise WMS integrations + strong retail/e-commerce customer roster |
| **Aethon (ST Engineering)** | Hospital / hospitality autonomous delivery | Extends Matradee and DUST-E into healthcare facility market |

---

## 4. Partnership Strategy

### 4.1 Active Engineering Partners

#### Ologic (Robot Engineering — Current Partner)
- **Deepen scope:** Move from project-based to a retained engineering arrangement with co-IP provisions on Dex actuator work
- **Joint roadmap:** Quarterly alignment on Dex's hardware spec so Ologic can pre-engineer tooling rather than react to changes
- **Data collaboration:** Ologic should be the teleoperation partner for early VLA data collection — they understand the kinematics

### 4.2 Vision and Perception

#### Oxipital AI (Precision Vision)
- **Use case fit:** Precision pick-and-place, barcode/label reading, quality inspection for Scorpion and logistics deployments
- **Integration path:** Embed Oxipital's vision stack as the default perception module in ADAM and Scorpion; negotiate OEM pricing tied to deployment volume
- **Strategic protection:** Get right-of-first-refusal on an exclusive partnership or preferred licensing agreement before a larger competitor locks them up

#### Additional Vision Partners to Evaluate

| Company | Capability | Fit |
|---------|-----------|-----|
| **Zivid** | High-accuracy 3D structured light | Scorpion industrial arm precision |
| **Luxonis** | Edge AI + depth cameras (OAK) | Low-cost Matradee and ADAM vision |
| **Prophesee** | Event cameras (low-latency visual sensing) | High-speed Dex manipulation |
| **Photoneo** | Motion-blurred scene capture | Moving conveyors, logistics |

### 4.3 Compute and Cloud Partners

Ready for Robots serves and partners with a growing Fortune 500 ecosystem spanning technology, hospitality, logistics, retail, and manufacturing. The three anchor relationships are listed below; the broader enterprise sales motion should target any Fortune 500 company with large physical facilities, labor-intensive operations, or existing robotics/automation programs.

#### NVIDIA
- **Products:** Jetson Orin for edge inference on Dex/ADAM/Titan; Isaac Sim for synthetic VLA training data; Cosmos for world-model pre-training
- **Partnership ask:** NVIDIA Inception → NVIDIA Partner Network → co-marketing around Dex as a flagship Jetson-powered humanoid and ADAM/Titan as reference platforms for Isaac ROS
- **Specific:** Negotiate GPU credits for VLA training; position Ready for Robots as a reference customer for Isaac Robotics; explore joint go-to-market for logistics and manufacturing accounts

#### Microsoft
- **Products:** Azure OpenAI Service (VLA inference in cloud), Azure Digital Twins (fleet modeling), Teams/Copilot integration for robot supervision dashboards
- **Customer and partner angle:** ADAM, Titan, DUST-E, and Scorpion as Azure-managed fleets in Microsoft campuses, data centers, and partner manufacturing/logistics sites; Dex as the showcase for Microsoft's physical AI narrative
- **Partnership ask:** Microsoft for Startups → ISV partner → co-selling through Azure Marketplace; explore positioning Ready for Robots robots within Microsoft's facilities management procurement

#### Apple
- **Products:** Vision Pro for immersive robot teleoperation, supervision, and training data collection; ARKit for environment mapping and robot path visualization
- **Partnership angle:** A Vision Pro operator interface that lets facilities managers supervise Dex, ADAM, and DUST-E fleets spatially — a genuinely differentiated enterprise pitch no competitor can replicate today
- **Near-term action:** Build Vision Pro companion app for Matradee and Dex fleet management; submit to App Store; engage Apple Enterprise accounts in hospitality and retail

#### Broader Fortune 500 Target Verticals

| Vertical | Target Companies | Best-Fit Robots |
|----------|-----------------|----------------|
| **Hotels / Hospitality** | Marriott, Hilton, IHG, Hyatt, MGM Resorts | Matradee, DUST-E, Dex |
| **Retail / Big Box** | Walmart, Target, Home Depot, Amazon | ADAM, Titan, DUST-E |
| **Healthcare** | HCA Healthcare, CommonSpirit, Mayo Clinic | DUST-E, ADAM, Matradee |
| **Logistics / 3PL** | UPS, FedEx, XPO, Ryder, Penske | ADAM, Titan, Scorpion |
| **Manufacturing** | GE, Ford, Honeywell, Siemens, Caterpillar | Scorpion, Dex, Titan |
| **Food & Beverage** | Compass Group, Sodexo, Aramark | Matradee, DUST-E |
| **Tech Campuses** | Google, Meta, Amazon, Salesforce | Full portfolio — flagship showcase sites |

### 4.4 Sector-Specific Partners

| Partner Type | Example Companies | Purpose |
|-------------|------------------|---------|
| **Hotel PMS / POS systems** | Oracle OPERA, Agilysys, Mews | Native Matradee integration → sticky hospitality sales |
| **WMS / ERP** | SAP, Manhattan Associates, Blue Yonder | ADAM and Scorpion enterprise sales via software attach |
| **Staffing agencies** | Sodexo, Aramark, Compass Group | Matradee as "labor productivity" solution, not replacement |
| **Delivery / last-mile networks** | DHL, FedEx Robotics, Locus | Co-deployment agreements for ADAM in fulfillment centers |
| **Integrators / VARs** | System integrators with hotel/logistics verticals | Sell-through channel for Matradee at scale |

---

## 5. Revenue Architecture

### 5.1 Revenue Streams

| Stream | Model | Margin Profile | Time to Scale |
|--------|-------|---------------|---------------|
| **Hardware sales** (Dex, ADAM, Titan, Scorpion, Matradee, DUST-E) | One-time + warranty | Medium (40–55%) | Now |
| **RaaS — Robot as a Service** | Monthly subscription per unit | High (70%+) | 6–12 months |
| **AI / Model licensing** | Per-API-call or annual license | Very High (80%+) | 12–24 months |
| **Data services** | Training data sold to OEMs/researchers | Very High | 18–36 months |
| **Maintenance & support** | Annual contract % of hardware value | Medium-High (60%) | Now |
| **Professional services** | Deployment, integration, training | Low-Medium (30–40%) | Now |

### 5.2 RaaS as the Anchor Strategy

One-time hardware sales limit recurring visibility. The goal is to convert all deployments to RaaS within 18 months:

- **Pricing model:** $X/robot/month inclusive of hardware, software, support, and model updates (bundled pricing removes the hardware capex barrier)
- **Key metrics to track:** Net Revenue Retention, robot utilization rate (% of hours robot is active), Signal-to-Deployment Time
- **Early movers by robot:**
  - **Matradee** — $1,500–$3,500/month; well-established price point in service robot market
  - **DUST-E** — $1,200–$2,500/month; labour replacement math is simple (1 robot = 1–2 FTE cleaning shifts); fastest ROI story
  - **ADAM / Titan** — $3,500–$8,000/month depending on payload and integration complexity; attach to WMS contract
  - **Scorpion** — $5,000–$12,000/month; price against UR/Fanuc leasing rates
  - **Dex** — $8,000–$20,000+/month once proven; humanoid premium justified by task versatility

### 5.3 Near-Term Revenue Priorities

**Q2–Q3 2026**
1. Close 3–5 Matradee enterprise pilots in hotel groups (Marriott, IHG, Hilton, MGM — facilities teams actively tracking this space)
2. Close 2–3 DUST-E pilots in hotels or healthcare — fastest labour-cost story to close
3. Sign 1–2 ADAM/Titan logistics pilots with a 3PL or fulfillment center for repeatable case study
4. Land first Scorpion inspection contract (automotive or aerospace)

**Q3–Q4 2026**
5. Convert pilots to multi-unit RaaS contracts
6. First OEM licensing conversation with a non-competing robot company (sell the VLA model, not just hardware)
7. Begin enterprise sales motion to NVIDIA, Microsoft, Apple, and Fortune 500 tech campus facilities teams using ADAM + DUST-E + Dex showcase
8. Advance LOI on logistics robot acquisition target

---

## 6. Competitive Positioning

### 6.1 Where Ready for Robots Competes

| Segment | Key Competitors | Differentiation |
|---------|----------------|-----------------|
| Hospitality service robots | Bear Robotics, Keenon, Pudu | Matradee + DUST-E combined offering; US-based support; proprietary AI layer |
| Cleaning / facilities robots | Tennant, Avidbots, Gaussian Robotics | DUST-E + FM integration; upgradeable to broader task set via VLA |
| Humanoid (general) | Figure AI, Agility, Boston Dynamics | Focused verticals (not trying to be general-purpose); VLA model tuned for service |
| Heavy AMR / Logistics | 6 River, Locus, GreyOrange, Vecna | Titan's payload capacity + ADAM's flexibility + VLA-driven pick integration |
| Industrial arm | Universal Robots, Fanuc, ABB | Lower cost, faster deployment, AI-native programming vs. teach-pendant |

### 6.2 Moat-Building Priorities (Ranked)

1. **Proprietary VLA training data** — once you have 100K task demonstrations others cannot easily replicate, the moat is structural
2. **Six-robot platform breadth** — Matradee, DUST-E, ADAM, Titan, Scorpion, and Dex means one Fortune 500 facilities relationship drives revenue across multiple product lines and budget categories (capex, opex, FM, logistics, manufacturing)
3. **Ologic + Oxipital embedded stack** — custom hardware + precision vision creates a vertically integrated solution that is hard to unbundle
4. **Customer fleet data** — every deployed robot improves the model for all robots; this flywheel accelerates with scale
5. **Logistics acquisition channel** — an acquired logistics robot company brings existing customer relationships, WMS integrations, and operational credibility that would take 3+ years to build organically

---

## 7. The Humanoid Inflection — Strategic and Economic Impact

### 7.1 Why Humanoids Change the Game

Humanoid robots are not simply stronger, more capable alternatives to task-specific AMRs. They represent a structural shift in the economics of automation: for the first time, a single robot platform can be **re-tasked across an entire facility** — unloading a truck, stocking shelves, cleaning a floor, serving food, and handling packages — without hardware changes. This has profound implications for how Ready for Robots prices, sells, and compounds value.

The consensus view from institutional robotics investors in early 2026 is that humanoid unit economics cross the commercial viability threshold (broadly compelling vs. human labour) between 2027 and 2030 for high-turnover, physically demanding roles. Ready for Robots is building toward that window now, with Dex as the platform.

### 7.2 The Economics of Humanoid Deployment

| Metric | Human Worker (US) | Task-Specific AMR | Humanoid (Dex, 2026 target) | Humanoid (Dex, 2028 projection) |
|--------|------------------|------------------|-----------------------------|---------------------------------|
| Annual all-in cost | $45,000–$65,000 | $18,000–$40,000 | $96,000–$240,000 | $36,000–$84,000 |
| Tasks per unit | 1 role | 1–2 roles | 10–20+ roles | 20–50+ roles |
| Operating hours/day | 8 (+ overtime) | 20–22 | 16–20 | 20–22 |
| Retraining cost | High | Full hardware swap | Software update | Software update |
| Labour risk (turnover) | High | None | None | None |

**Key insight:** A single Dex unit priced at $8,000–$15,000/month on RaaS — replacing two to three roles at a hotel, fulfillment center, or hospital — delivers a positive economic case in high-labour-cost markets as early as 2026. The RaaS price declines as unit costs fall with manufacturing scale, while the value delivered expands as the VLA model improves. This creates a **widening unit economics curve** that accelerates customer acquisition over time.

### 7.3 Humanoids as the Unifying Platform for the Full Portfolio

One of the most important — and underappreciated — strategic implications is that Dex's success creates value for every other product in the portfolio:

- **VLA model trained on Dex** can be fine-tuned into Scorpion arm tasks at low cost → Scorpion gets smarter without separate training investment
- **Operational data from ADAM/Titan/Matradee** deployments informs Dex navigation and environment understanding in the same customer facilities
- **DUST-E's cleaning task library** is a natural early dataset for Dex's own cleaning capability — cross-pollination of training data across the portfolio
- **A Fortune 500 customer that deploys Matradee today** is the natural first Dex enterprise customer — the relationship, facility map, and IT integration are already in place

This means the portfolio is not six separate products — it is one compounding platform. Each robot deployed is a data node, a customer relationship, and a stepping stone for Dex adoption.

### 7.4 Humanoid Opportunities by Vertical

| Vertical | Near-Term Dex Use Cases | Labour Substitution Economics | Timeline to Viable |
|----------|------------------------|------------------------------|-------------------|
| **Hospitality** | Room setup/turnover, luggage handling, linen transport, concierge tasks | Housekeeper: $35–50K/yr; Dex replaces 1.5–2 FTE | 2026–2027 |
| **Logistics / Fulfillment** | Pick-and-place, packing, unloading trailers, returns processing | Picker: $40–55K/yr; Dex handles 200–400 picks/hr | 2026–2027 |
| **Food Service** | Food prep assistance, dishwashing, ingredient handling | Line cook / dishwasher: $32–45K/yr | 2027–2028 |
| **Healthcare / Senior Living** | Patient transport assist, linen, supply replenishment | CNA aide tasks: $35–50K/yr; high-turnover role | 2027–2028 |
| **Retail / Facilities** | Restocking, cycle counting, spill response | Stock associate: $28–38K/yr; overnight tasks | 2027–2028 |

### 7.5 Strategic Implications for the 3-Year Plan

1. **Price the full fleet to win facilities, not individual robots** — a CFO who signs a DUST-E + Matradee + ADAM contract today is implicitly buying into the Dex roadmap. Structure multi-robot contracts with Dex upgrade rights built in.

2. **Dex is the ultimate upsell motion** — every task-specific robot (DUST-E, Matradee, ADAM, Titan) sold today is market development for Dex. The customer's facility is already mapped; their staff are already trained on robot supervision; their procurement has already approved robot spend.

3. **The VLA model is the real product** — as humanoid hardware commoditizes (manufacturing costs fall 40–60% by 2028 based on current trajectories), the differentiator will be the model, the data, and the task library. Competitors who own the hardware but not the model will be squeezed. Ready for Robots must own the model.

4. **Dex creates a new M&A target class** — companies with large, structured physical task environments (hotel management companies, 3PL operators, healthcare networks) become strategic acquisition or JV targets because they provide both the deployment channel and the training data generation engine simultaneously.

---

## 8. Technology Stack Gaps and Recommended Actions

| Gap | Current State | Recommended Action | Timeline |
|-----|-------------|-------------------|----------|
| **VLA foundation model** | None in-house | Invest in Reflex/DYNA; begin teleoperation data collection with Ologic | Q2 2026 |
| **Simulation environment** | None | License NVIDIA Isaac Sim; begin synthetic data generation | Q2 2026 |
| **Precision vision** | Evaluating Oxipital | Sign OEM agreement; integrate into ADAM and Scorpion | Q3 2026 |
| **Edge inference hardware** | TBD | Standardize on NVIDIA Jetson Orin platform-wide | Q2 2026 |
| **Fleet management software** | Early stage | Build or acquire basic dashboard; integrate with Azure Digital Twins | Q3 2026 |
| **Force/torque sensing for Dex** | Unknown | Partner with ATI Industrial or OnRobot for wrist F/T sensors | Q3 2026 |
| **Human presence / safety AI** | Unknown | Evaluate Voxel51, SICK Safety, or custom | Q3 2026 |

---

## 9. Key Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Reflex or DYNA acquired by a strategic (Nvidia, Amazon, Figure) before deal closes | Medium | High | Move fast; get term sheet or exclusivity in place |
| VLA model training takes longer / costs more than projected | Medium | High | Parallel track: license Pi or Google RT-2 while training proprietary model |
| Hardware cost too high for RaaS margin target | Low-Medium | High | Ologic co-design to reduce BOM; volume commitments to suppliers |
| Microsoft or Apple partnerships take 12+ months to materialize | High | Medium | Start with direct sales to their facilities; enterprise partnership follows revenue |
| Competitive humanoid entrants commoditize manipulation AI | Low | High | Data moat — focus on number of demonstrations, not just model architecture |
| Logistics robot acquisition target gets acquired by Amazon/Walmart first | Medium | High | Begin outreach immediately; prioritize companies without inbound VC pressure to sell to strategics |
| DUST-E fails to displace incumbent cleaning contracts | Low-Medium | Medium | Price below human labor cost; offer 90-day pilot with full cancellation rights to reduce adoption friction |

---

## 10. 90-Day Action Plan

### Immediately (March 2026)
- [ ] Begin acquisition/investment outreach to **Reflex Robotics** and **DYNA** — set NDAs and initial discovery calls
- [ ] Begin sourcing process for **logistics robot acquisition** — identify 5–10 candidates; prioritize companies with existing 3PL/fulfillment contracts
- [ ] Define Ologic's teleoperation scope for Dex VLA data collection — target 1,000 task demonstrations by end of Q2
- [ ] Negotiate Oxipital OEM agreement — request pilot hardware for integration into ADAM and Titan prototypes
- [ ] Apply for **NVIDIA Inception** and **Microsoft for Startups** programs
- [ ] Initiate DUST-E hotel pilot outreach — target 2–3 properties in a managed hotel group

### 30 Days
- [ ] Select simulation platform (Isaac Sim vs. MuJoCo/Genesis) — stand up internal environment for synthetic data generation
- [ ] Define Matradee RaaS pricing model and pilot contract terms
- [ ] Document Dex motion capability gaps vs. target task library — this becomes the VLA training spec
- [ ] Identify 5 target hotel groups for Matradee enterprise pilots

### 60 Days
- [ ] First teleoperation session with Ologic on Dex — begin capturing dexterous manipulation demonstrations
- [ ] Close at least one Matradee pilot contract (RaaS model)
- [ ] Deliver Vision Pro companion app prototype to Apple Enterprise contacts
- [ ] Complete initial evaluation of Oxipital integration on ADAM

### 90 Days
- [ ] Reach investment or LOI milestone with Reflex or DYNA
- [ ] Have 5,000+ Dex task demonstrations in dataset
- [ ] Close first ADAM or Titan logistics pilot contract
- [ ] Close first DUST-E hotel or healthcare pilot contract (RaaS)
- [ ] Reach term sheet stage on logistics robot acquisition
- [ ] Publish initial VLA benchmarks for internal roadmap alignment
- [ ] Complete Humanoid Deployment Playbook — Dex task library, labour substitution calculator, and ROI model for enterprise sales team

---

## 11. Summary: The Long Game

Ready for Robots is positioned at the intersection of three massive secular shifts — the robotization of the service economy, the emergence of generalizable foundation models for physical AI, and the approaching commercial viability of humanoid robots. The companies that win this decade will be those that:

1. **Own the model** — not just the hardware; VLA model weights trained on proprietary demonstrations are the IP that accrues value as humanoid hardware commoditizes
2. **Own the data** — every deployed robot across the full six-product fleet is a data collection asset; scale deployments relentlessly
3. **Own the vertical** — deep integration with hospitality and logistics software ecosystems, and relationships with a growing Fortune 500 customer base, makes displacement by a hardware-only competitor nearly impossible
4. **Move fast on M&A** — Reflex, DYNA, and the logistics robot acquisition are not the last windows; the consolidation of robotics AI and logistics automation is happening now and the window to acquire capabilities at reasonable valuations is 12–18 months
5. **Lead on humanoids** — Dex is not just one product; it is the platform that eventually re-tasks across every environment where the other five robots operate today, and its success creates a widening economic and data moat that competitors building single-purpose machines cannot match

The technology stack built around the six-robot portfolio + VLA + Oxipital vision + NVIDIA compute + Ologic hardware engineering creates a defensible, compounding asset — but only if data collection, model development, and the logistics acquisition process begin immediately.

**The humanoid inflection is coming regardless.** The strategic question is whether Ready for Robots arrives at that moment with a trained model, a Fortune 500 customer base, and a proprietary data flywheel — or having ceded that ground to a well-funded competitor.

---

*Last updated: March 2026 | For internal use only*
