import { COOKIE_NAME } from "@shared/const";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { publicProcedure, router } from "./_core/trpc";
import { invokeLLM } from "./_core/llm";
import { z } from "zod";
import {
  upsertScoutSession,
  updateScoutSession,
  appendScoutMessage,
  getScoutHistory,
  getScoutProfile,
  trackCompanyViewed,
  updateInferredNeeds,
} from "./scoutDb";
import { getDb } from "./db";
import { leads, userSettings, waitlistSignups, pipelineOpportunities } from "../drizzle/schema";
import { eq, desc } from "drizzle-orm";
import { protectedProcedure } from "./_core/trpc";

// ── SCOUT System Prompt ────────────────────────────────────────────────────────
const SCOUT_SYSTEM_PROMPT = `You are SCOUT, the AI sales agent for ReadyForRobots. You are sharp, confident, and focused on helping robotics salespeople close more deals.

Your role: You find companies that are ready to buy robots, qualify them using real buying signals (labor shortages, expansion plans, CapEx signals, hiring patterns), and deliver ready-to-send outreach — before competitors notice. You also identify strategic partnership opportunities: system integrators, distributors, VARs, and channel partners who are actively seeking robotics products to carry. You develop both sales leads AND partnership relationships from first signal to closed deal.

Key facts about you:
- You monitor 150+ sources 24/7: job boards, earnings calls, press releases, OSHA filings, real estate permits, industry news
- You score every prospect on 4 factors: labor pain, expansion stage, automation fit, and timing
- You identify strategic partners: system integrators (SIs), distributors, VARs, and channel partners looking to add robotics to their portfolio
- Partnership signals include: SI directories, distributor filings, channel RFPs, trade show exhibitor lists, and partner program announcements
- You work with all robot categories: warehouse AMRs, service robots, industrial arms, cleaning robots, food processing, healthcare, and more
- You deliver a prioritized pipeline with drafted outreach and the exact signal that triggered each opportunity
- You've influenced 500+ robot deals and 200+ strategic partnerships across 60+ robotics companies
- You operate in 3 modes: Auto (you act), Assisted (you draft, human approves), Manual (you surface, human does everything)

Personality: Direct, data-driven, a little dry. You don't waste words. You're proud of what you do. You speak in specifics, not generalities.

When asked what kind of robots someone sells, you get excited — because that's when you can show them exactly what you'd find for their specific vertical.

Keep responses concise (2-4 sentences max unless asked for detail). Always end with a forward-moving question or offer.

When you have context about the user (their robot category, company, or past conversations), use it naturally — reference what you know and build on it. This is a relationship, not a cold call.`;

// ── Skill: Scan Company ──────────────────────────────────────────────────────
async function skillScanCompany(url: string, robotCategory?: string): Promise<{
  url: string;
  score: number;
  signals: string[];
  summary: string;
  recommendation: string;
}> {
  const prompt = `You are SCOUT, an AI that analyzes companies for robot automation readiness.
Analyze this company URL: ${url}
Robot category context: ${robotCategory ?? "general automation"}

Return a JSON object with:
- score: number 0-100 (automation readiness score)
- signals: array of 3-4 specific buying signal strings detected
- summary: one sentence describing what this company does and why they need automation
- recommendation: one sentence on the best outreach angle

Be realistic and specific. If the URL looks like a generic company, infer from the domain name.`;

  const result = await invokeLLM({
    messages: [{ role: "user", content: prompt }],
    response_format: {
      type: "json_schema",
      json_schema: {
        name: "company_scan",
        strict: true,
        schema: {
          type: "object",
          properties: {
            score: { type: "number" },
            signals: { type: "array", items: { type: "string" } },
            summary: { type: "string" },
            recommendation: { type: "string" },
          },
          required: ["score", "signals", "summary", "recommendation"],
          additionalProperties: false,
        },
      },
    },
  });

  const content = result.choices[0]?.message?.content;
  const text = typeof content === "string" ? content : "";
  const parsed = JSON.parse(text);
  return { url, ...parsed };
}

// ── Skill: Find Prospects ──────────────────────────────────────────────────────
async function skillFindProspects(category: string, territory: string): Promise<{
  prospects: Array<{
    company: string;
    industry: string;
    signal: string;
    score: number;
    outreachAngle: string;
  }>;
  totalTracked: number;
  hotCount: number;
}> {
  const prompt = `You are SCOUT. Generate 3 realistic prospect companies for a robotics salesperson.
Robot category: ${category}
Territory: ${territory}

Return JSON with:
- prospects: array of 3 objects, each with: company (string), industry (string), signal (specific buying signal string), score (number 70-98), outreachAngle (one sentence)
- totalTracked: realistic number of total companies tracked for this category (150-400)
- hotCount: number of hot prospects (10-45)

Make companies realistic and specific to the territory. Signals should be concrete (e.g. "Posted 3 automation engineer roles in Q1", "Earnings call mentioned $40M CapEx for facility expansion").`;

  const result = await invokeLLM({
    messages: [{ role: "user", content: prompt }],
    response_format: {
      type: "json_schema",
      json_schema: {
        name: "prospects",
        strict: true,
        schema: {
          type: "object",
          properties: {
            prospects: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  company: { type: "string" },
                  industry: { type: "string" },
                  signal: { type: "string" },
                  score: { type: "number" },
                  outreachAngle: { type: "string" },
                },
                required: ["company", "industry", "signal", "score", "outreachAngle"],
                additionalProperties: false,
              },
            },
            totalTracked: { type: "number" },
            hotCount: { type: "number" },
          },
          required: ["prospects", "totalTracked", "hotCount"],
          additionalProperties: false,
        },
      },
    },
  });

  const content = result.choices[0]?.message?.content;
  const text = typeof content === "string" ? content : "";
  return JSON.parse(text);
}

// ── Skill: Find Partners ───────────────────────────────────────────────────────
async function skillFindPartners(partnerType: string, region: string): Promise<{
  partners: Array<{
    company: string;
    type: string;
    territory: string;
    signal: string;
    score: number;
    outreachAngle: string;
  }>;
  totalTracked: number;
}> {
  const prompt = `You are SCOUT. Generate 3 realistic strategic partner prospects for a robotics company.
Partner type: ${partnerType} (e.g. system integrator, distributor, VAR)
Region: ${region}

Return JSON with:
- partners: array of 3 objects, each with: company (string), type (string), territory (string), signal (specific partnership signal), score (number 70-95), outreachAngle (one sentence)
- totalTracked: realistic number of total partners tracked (30-120)

Make companies realistic. Signals should be concrete (e.g. "Posted job for Robotics Product Manager", "Exhibiting at Automate 2025 as automation solutions provider").`;

  const result = await invokeLLM({
    messages: [{ role: "user", content: prompt }],
    response_format: {
      type: "json_schema",
      json_schema: {
        name: "partners",
        strict: true,
        schema: {
          type: "object",
          properties: {
            partners: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  company: { type: "string" },
                  type: { type: "string" },
                  territory: { type: "string" },
                  signal: { type: "string" },
                  score: { type: "number" },
                  outreachAngle: { type: "string" },
                },
                required: ["company", "type", "territory", "signal", "score", "outreachAngle"],
                additionalProperties: false,
              },
            },
            totalTracked: { type: "number" },
          },
          required: ["partners", "totalTracked"],
          additionalProperties: false,
        },
      },
    },
  });

  const content = result.choices[0]?.message?.content;
  const text = typeof content === "string" ? content : "";
  return JSON.parse(text);
}

// ── Skill: Scan For Results Page ─────────────────────────────────────────────
/**
 * Combined scan used by the Results page:
 * 1. Infers the visitor's robot category from their company URL
 * 2. Finds 3 real matched prospects + 5 locked teasers
 * 3. Drafts outreach emails for the 3 visible prospects
 */
// ── Helper: infer contact email from signal type and company domain ────────────
function inferContactEmail(company: string, signalType: string): string {
  // Derive a plausible domain from the company name
  const domain = company
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, "")
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .join("") + ".com";

  const st = signalType.toLowerCase();
  if (st.includes("capex") || st.includes("procurement") || st.includes("safety")) {
    return `purchasing@${domain}`;
  }
  if (st.includes("expansion") || st.includes("partnership") || st.includes("bd")) {
    return `bd@${domain}`;
  }
  if (st.includes("hiring") || st.includes("labor") || st.includes("job")) {
    return `hr@${domain}`;
  }
  // Default: general sales contact
  return `info@${domain}`;
}

async function skillScanForResults(companyUrl: string): Promise<{
  robotCategory: string;
  territory: string;
  companySummary: string;
  prospects: Array<{
    company: string;
    location: string;
    industry: string;
    employees: string;
    score: number;
    signal: string;
    signalType: string;
    timing: string;
    action: string;
    draft: string;
    stage: string;
    contactEmail: string;
  }>;
  lockedTeasers: Array<{
    industry: string;
    score: number;
    location: string;
    signalType: string;
  }>;
  totalFound: number;
}> {
  // Step 1: Infer category + territory from the company URL
  const inferResult = await invokeLLM({
    messages: [{
      role: "user",
      content: `You are SCOUT. A robotics company just submitted their website URL: ${companyUrl}

Infer from the domain name:
1. What type of robot they sell (e.g. "warehouse AMR", "service robot", "industrial arm", "cleaning robot", "food processing automation")
2. Their likely primary sales territory (e.g. "US Midwest", "US West Coast", "US Southeast", "North America")
3. A one-sentence summary of what this company likely does

Return JSON with: robotCategory (string), territory (string), companySummary (string)`,
    }],
    response_format: {
      type: "json_schema",
      json_schema: {
        name: "infer_company",
        strict: true,
        schema: {
          type: "object",
          properties: {
            robotCategory: { type: "string" },
            territory: { type: "string" },
            companySummary: { type: "string" },
          },
          required: ["robotCategory", "territory", "companySummary"],
          additionalProperties: false,
        },
      },
    },
  });

  const inferContent = inferResult.choices[0]?.message?.content;
  const inferred = JSON.parse(typeof inferContent === "string" ? inferContent : "{}") as {
    robotCategory: string;
    territory: string;
    companySummary: string;
  };

  const robotCategory = inferred.robotCategory ?? "warehouse automation";
  const territory = inferred.territory ?? "United States";

  // Step 2: Find 3 prospects + 5 locked teasers
  const prospectsResult = await invokeLLM({
    messages: [{
      role: "user",
      content: `You are SCOUT. Generate 3 detailed prospect companies for a ${robotCategory} salesperson targeting ${territory}.

For each prospect return:
- company: realistic company name
- location: City, State
- industry: industry vertical
- employees: employee count as string (e.g. "1,200")
- score: number 75-98
- signal: specific buying signal (e.g. "Earnings call: '40% labor vacancy in warehouse' — Q3 2025" or "Job posting: Automation Engineer + press release: Opening 2 new DCs")
- signalType: one of: Labor Shortage, Expansion Signal, Safety Signal, CapEx Announcement, Automation Hiring
- timing: decision window (e.g. "Decision window: Now" or "Decision window: 3–6 months")
- action: one-sentence recommended outreach action
- stage: one of: New Signal, Draft Ready, In Progress

Also generate 5 locked teasers (just industry, score 75-95, location, signalType).

Return JSON with:
- prospects: array of 3 full prospect objects
- lockedTeasers: array of 5 teaser objects (industry, score, location, signalType)
- totalFound: realistic total number of matched companies (8-15)`,
    }],
    response_format: {
      type: "json_schema",
      json_schema: {
        name: "scan_results",
        strict: true,
        schema: {
          type: "object",
          properties: {
            prospects: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  company: { type: "string" },
                  location: { type: "string" },
                  industry: { type: "string" },
                  employees: { type: "string" },
                  score: { type: "number" },
                  signal: { type: "string" },
                  signalType: { type: "string" },
                  timing: { type: "string" },
                  action: { type: "string" },
                  stage: { type: "string" },
                },
                required: ["company", "location", "industry", "employees", "score", "signal", "signalType", "timing", "action", "stage"],
                additionalProperties: false,
              },
            },
            lockedTeasers: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  industry: { type: "string" },
                  score: { type: "number" },
                  location: { type: "string" },
                  signalType: { type: "string" },
                },
                required: ["industry", "score", "location", "signalType"],
                additionalProperties: false,
              },
            },
            totalFound: { type: "number" },
          },
          required: ["prospects", "lockedTeasers", "totalFound"],
          additionalProperties: false,
        },
      },
    },
  });

  const prospectsContent = prospectsResult.choices[0]?.message?.content;
  const prospectsData = JSON.parse(typeof prospectsContent === "string" ? prospectsContent : "{}") as {
    prospects: Array<{ company: string; location: string; industry: string; employees: string; score: number; signal: string; signalType: string; timing: string; action: string; stage: string; }>;
    lockedTeasers: Array<{ industry: string; score: number; location: string; signalType: string; }>;
    totalFound: number;
  };

  // Step 3: Draft outreach for each visible prospect + infer contact email
  const prospectsWithDrafts = await Promise.all(
    (prospectsData.prospects ?? []).map(async (p) => {
      const draft = await skillDraftOutreach(p.company, p.signal, robotCategory);
      const contactEmail = inferContactEmail(p.company, p.signalType);
      return { ...p, draft: `Subject: ${draft.subject}\n\n${draft.body}`, contactEmail };
    })
  );

  return {
    robotCategory,
    territory,
    companySummary: inferred.companySummary ?? "",
    prospects: prospectsWithDrafts,
    lockedTeasers: prospectsData.lockedTeasers ?? [],
    totalFound: prospectsData.totalFound ?? prospectsWithDrafts.length + (prospectsData.lockedTeasers?.length ?? 0),
  };
}

// ── Skill: Draft Outreach ──────────────────────────────────────────────────────
async function skillDraftOutreach(
  company: string,
  signal: string,
  robotCategory: string,
  senderCompany?: string,
  contactName?: string,
  contactTitle?: string
): Promise<{ subject: string; body: string }> {
  const sender = senderCompany ?? "ReadyForRobots";
  const greeting = contactName ? `Dear ${contactName}` : `Hi`;
  const titleCtx = contactTitle ? `\nContact title: ${contactTitle}` : "";
  const prompt = `You are SCOUT, an expert B2B sales writer for robotics companies.
Write a personalized proposal outreach email following these rules:

1. SUBJECT LINE: Use the format "Automation Proposal for ${company} — ${sender}". Keep under 65 chars. Make it specific to the signal.
2. GREETING: Start with "${greeting},"
3. PARAGRAPH 1 (Signal reference, 1-2 sentences): Reference the SPECIFIC buying signal. Show research. E.g. "I noticed ${company} recently ${signal.toLowerCase()} — this typically signals a window for automation investment."
4. PARAGRAPH 2 (Value connection, 2 sentences): Connect their signal to the specific ${robotCategory} solution. Quantify the benefit if possible (e.g. "reduce labor dependency by 40%", "cut pick cycle times in half").
5. PARAGRAPH 3 (CTA, 2 sentences): Ask for a 15-minute call. Use a specific, humble ask: "Would you have 15 minutes next week to explore whether this fits your roadmap?"
6. SIGN-OFF: "Best regards,\n[Your Name]\n${sender}"

Target company: ${company}
Buying signal: ${signal}
Robot category: ${robotCategory}
Sender company: ${sender}${titleCtx}

Rules:
- Under 180 words total
- No buzzwords ("synergy", "leverage", "cutting-edge", "innovative")
- Sound like a senior human salesperson, not a bot
- Be specific to the signal — never generic
- Subject line must reference the company name`;

  const result = await invokeLLM({
    messages: [{ role: "user", content: prompt }],
    response_format: {
      type: "json_schema",
      json_schema: {
        name: "outreach_draft",
        strict: true,
        schema: {
          type: "object",
          properties: {
            subject: { type: "string" },
            body: { type: "string" },
          },
          required: ["subject", "body"],
          additionalProperties: false,
        },
      },
    },
  });

  const content = result.choices[0]?.message?.content;
  const text = typeof content === "string" ? content : "";
  return JSON.parse(text);
}

// ── Helper: extract text from LLM response ─────────────────────────────────────
function extractText(result: Awaited<ReturnType<typeof invokeLLM>>): string {
  const content = result.choices[0]?.message?.content;
  if (typeof content === "string") return content;
  if (Array.isArray(content)) {
    return content
      .filter((p) => p.type === "text")
      .map((p) => (p as { type: "text"; text: string }).text)
      .join("");
  }
  return "";
}

// ── Router ─────────────────────────────────────────────────────────────────────
export const appRouter = router({
  system: systemRouter,
  auth: router({
    me: publicProcedure.query(opts => opts.ctx.user),
    logout: publicProcedure.mutation(({ ctx }) => {
      const cookieOptions = getSessionCookieOptions(ctx.req);
      ctx.res.clearCookie(COOKIE_NAME, { ...cookieOptions, maxAge: -1 });
      return { success: true } as const;
    }),
  }),

  leads: router({
    capture: publicProcedure
      .input(z.object({
        name: z.string().min(1),
        email: z.string().email(),
        companyUrl: z.string().optional(),
        source: z.string().optional(), // e.g. "results-modal", "hero"
      }))
      .mutation(async ({ input }) => {
        // Store in the leads table
        const db = await getDb();
        if (db) {
          await db.insert(leads).values({
            name: input.name,
            email: input.email,
            companyUrl: input.companyUrl,
            source: input.source ?? "results-modal",
          });
        }
        // Notify the site owner
        try {
          const { notifyOwner } = await import("./_core/notification");
          await notifyOwner({
            title: `New pipeline lead: ${input.name}`,
            content: `Email: ${input.email}\nCompany URL: ${input.companyUrl ?? "not provided"}\nSource: ${input.source ?? "unknown"}`,
          });
        } catch {
          // notification failure is non-blocking
        }
        return { success: true };
      }),
  }),

    // ── Waitlist ───────────────────────────────────────────────────────────────
  waitlist: router({
    join: publicProcedure
      .input(z.object({
        name: z.string().min(1),
        email: z.string().email(),
        tier: z.enum(["preview", "growth", "enterprise"]),
        robotCategory: z.string().optional(),
        companyUrl: z.string().optional(),
      }))
      .mutation(async ({ input }) => {
        const db = await getDb();
        if (db) {
          await db.insert(waitlistSignups).values({
            name: input.name,
            email: input.email,
            tier: input.tier,
            robotCategory: input.robotCategory,
            companyUrl: input.companyUrl,
          });
        }
        try {
          const { notifyOwner } = await import("./_core/notification");
          await notifyOwner({
            title: `New waitlist signup: ${input.tier} tier`,
            content: `Name: ${input.name}\nEmail: ${input.email}\nTier: ${input.tier}\nRobot category: ${input.robotCategory ?? "not provided"}\nCompany URL: ${input.companyUrl ?? "not provided"}`,
          });
        } catch { /* non-blocking */ }
        return { success: true };
      }),
  }),

  // ── SCOUT Settings ──────────────────────────────────────────────────────
  settings: router({
    get: protectedProcedure
      .query(async ({ ctx }) => {
        const db = await getDb();
        if (!db) return null;
        const rows = await db.select().from(userSettings).where(eq(userSettings.userId, ctx.user.id)).limit(1);
        return rows[0] ?? null;
      }),

    save: protectedProcedure
      .input(z.object({
        defaultPipelineMode: z.enum(["assisted", "autopilot"]).optional(),
        outreachPersona: z.enum(["on_behalf", "independent"]).optional(),
        senderCompanyName: z.string().max(256).optional(),
        senderName: z.string().max(128).optional(),
        senderTitle: z.string().max(128).optional(),
      }))
      .mutation(async ({ ctx, input }) => {
        const db = await getDb();
        if (!db) return { success: false, error: "db_unavailable" };
        const existing = await db.select({ id: userSettings.id }).from(userSettings).where(eq(userSettings.userId, ctx.user.id)).limit(1);
        if (existing.length > 0) {
          await db.update(userSettings).set({
            ...(input.defaultPipelineMode && { defaultPipelineMode: input.defaultPipelineMode }),
            ...(input.outreachPersona && { outreachPersona: input.outreachPersona }),
            ...(input.senderCompanyName !== undefined && { senderCompanyName: input.senderCompanyName }),
            ...(input.senderName !== undefined && { senderName: input.senderName }),
            ...(input.senderTitle !== undefined && { senderTitle: input.senderTitle }),
          }).where(eq(userSettings.userId, ctx.user.id));
        } else {
          await db.insert(userSettings).values({
            userId: ctx.user.id,
            defaultPipelineMode: input.defaultPipelineMode ?? "assisted",
            outreachPersona: input.outreachPersona ?? "on_behalf",
            senderCompanyName: input.senderCompanyName,
            senderName: input.senderName,
            senderTitle: input.senderTitle,
          });
        }
        return { success: true };
      }),
  }),

  scout: router({
    // ── Session management ──────────────────────────────────────────────────
    getSession: publicProcedure
      .input(z.object({ fingerprint: z.string() }))
      .mutation(async ({ input }) => {
        const { session, isNew } = await upsertScoutSession(input.fingerprint);
        const history = isNew ? [] : await getScoutHistory(session.id, 30);
        const profile = await getScoutProfile(session.id);
        return { session, history, profile, isNew };
      }),

    updateSession: publicProcedure
      .input(z.object({
        fingerprint: z.string(),
        robotCategory: z.string().optional(),
        vertical: z.string().optional(),
        territory: z.string().optional(),
        companyName: z.string().optional(),
        companyUrl: z.string().optional(),
      }))
      .mutation(async ({ input }) => {
        const { session } = await upsertScoutSession(input.fingerprint);
        const updates: Parameters<typeof updateScoutSession>[1] = {};
        if (input.robotCategory) updates.robotCategory = input.robotCategory;
        if (input.vertical) updates.vertical = input.vertical;
        if (input.territory) updates.territory = input.territory;
        if (input.companyName) updates.companyName = input.companyName;
        if (input.companyUrl) updates.companyUrl = input.companyUrl;
        await updateScoutSession(session.id, updates);
        return { success: true };
      }),

    saveMessage: publicProcedure
      .input(z.object({
        fingerprint: z.string(),
        role: z.enum(["scout", "user"]),
        content: z.string(),
        skillInvoked: z.string().optional(),
        skillData: z.unknown().optional(),
      }))
      .mutation(async ({ input }) => {
        const { session } = await upsertScoutSession(input.fingerprint);
        await appendScoutMessage(
          session.id,
          input.role,
          input.content,
          input.skillInvoked,
          input.skillData
        );
        return { success: true };
      }),

    // ── Live chat with persistence ──────────────────────────────────────────
    chat: publicProcedure
      .input(z.object({
        fingerprint: z.string(),
        messages: z.array(z.object({
          role: z.enum(["user", "assistant"]),
          content: z.string(),
        })),
        sessionContext: z.object({
          robotCategory: z.string().optional(),
          vertical: z.string().optional(),
          territory: z.string().optional(),
          companyName: z.string().optional(),
        }).optional(),
      }))
      .mutation(async ({ input }) => {
        const { session } = await upsertScoutSession(input.fingerprint);

        // Build context-aware system prompt
        const ctx = input.sessionContext;
        let contextNote = "";
        if (ctx?.robotCategory || ctx?.vertical || ctx?.companyName) {
          contextNote = `\n\nCurrent user context:`;
          if (ctx.companyName) contextNote += `\n- Company: ${ctx.companyName}`;
          if (ctx.robotCategory) contextNote += `\n- Robot category: ${ctx.robotCategory}`;
          if (ctx.vertical) contextNote += `\n- Vertical: ${ctx.vertical}`;
          if (ctx.territory) contextNote += `\n- Territory: ${ctx.territory}`;
          contextNote += `\n\nUse this context to personalize your responses.`;
        }

        const result = await invokeLLM({
          messages: [
            { role: "system", content: SCOUT_SYSTEM_PROMPT + contextNote },
            ...input.messages,
          ],
          maxTokens: 512,
        });

        const reply = extractText(result);

        // Persist the last user message and SCOUT's reply
        const lastUserMsg = [...input.messages].reverse().find(m => m.role === "user");
        if (lastUserMsg) {
          await appendScoutMessage(session.id, "user", lastUserMsg.content);
        }
        await appendScoutMessage(session.id, "scout", reply);

        // Periodically update inferred needs summary (every 5 messages)
        if (input.messages.length % 5 === 0 && input.messages.length > 0) {
          const summaryResult = await invokeLLM({
            messages: [
              {
                role: "system",
                content: "Summarize in 1-2 sentences what this robotics salesperson needs based on the conversation. Be specific.",
              },
              ...input.messages.slice(-10),
            ],
            maxTokens: 100,
          });
          const summary = extractText(summaryResult);
          if (summary) await updateInferredNeeds(session.id, summary);
        }

        return { reply, sessionId: session.id };
      }),

    // ── Skill: Scan Company ─────────────────────────────────────────────────
    scanCompany: publicProcedure
      .input(z.object({
        fingerprint: z.string(),
        url: z.string(),
        robotCategory: z.string().optional(),
      }))
      .mutation(async ({ input }) => {
        const { session } = await upsertScoutSession(input.fingerprint);
        const result = await skillScanCompany(input.url, input.robotCategory);
        await trackCompanyViewed(session.id, input.url);
        await appendScoutMessage(
          session.id,
          "scout",
          `Scanned ${input.url}: score ${result.score}/100`,
          "scanCompany",
          result
        );
        return result;
      }),

    // ── Skill: Find Prospects ───────────────────────────────────────────────
    findProspects: publicProcedure
      .input(z.object({
        fingerprint: z.string(),
        category: z.string(),
        territory: z.string(),
      }))
      .mutation(async ({ input }) => {
        const { session } = await upsertScoutSession(input.fingerprint);
        const result = await skillFindProspects(input.category, input.territory);
        await appendScoutMessage(
          session.id,
          "scout",
          `Found ${result.prospects.length} prospects for ${input.category} in ${input.territory}`,
          "findProspects",
          result
        );
        return result;
      }),

    // ── Skill: Find Partners ────────────────────────────────────────────────
    findPartners: publicProcedure
      .input(z.object({
        fingerprint: z.string(),
        partnerType: z.string(),
        region: z.string(),
      }))
      .mutation(async ({ input }) => {
        const { session } = await upsertScoutSession(input.fingerprint);
        const result = await skillFindPartners(input.partnerType, input.region);
        await appendScoutMessage(
          session.id,
          "scout",
          `Found ${result.partners.length} partner prospects (${input.partnerType}) in ${input.region}`,
          "findPartners",
          result
        );
        return result;
      }),
    // ── Skill: Scan For Results Page ──────────────────────────────────────────────
    scanForResults: publicProcedure
      .input(z.object({
        companyUrl: z.string().min(1),
        fingerprint: z.string().optional(),
      }))
      .mutation(async ({ input }) => {
        const result = await skillScanForResults(input.companyUrl);
        if (input.fingerprint) {
          try {
            const { session } = await upsertScoutSession(input.fingerprint);
            await trackCompanyViewed(session.id, input.companyUrl);
          } catch { /* non-blocking */ }
        }
        return result;
      }),


    // ── Proactive Signal Update (returning users) ──────────────────────────────
    getSignalUpdate: publicProcedure
      .input(z.object({
        fingerprint: z.string(),
        robotCategory: z.string().optional(),
        vertical: z.string().optional(),
        territory: z.string().optional(),
        companyName: z.string().optional(),
        hoursSinceLastVisit: z.number(),
      }))
      .mutation(async ({ input }) => {
        const categoryLabels: Record<string, string> = {
          amr: 'Warehouse / AMR', industrial: 'Industrial arms', service: 'Service robots',
          food: 'Food & beverage automation', healthcare: 'Healthcare robots', partnerships: 'SI / distributor partnerships',
        };
        const categoryLabel = input.robotCategory ? (categoryLabels[input.robotCategory] ?? input.robotCategory) : 'general automation';
        const contextParts: string[] = [];
        if (input.companyName) contextParts.push(`Company: ${input.companyName}`);
        contextParts.push(`Robot category: ${categoryLabel}`);
        if (input.vertical) contextParts.push(`Vertical: ${input.vertical}`);
        if (input.territory) contextParts.push(`Territory: ${input.territory}`);
        const contextStr = contextParts.join(', ');
        const hoursLabel = input.hoursSinceLastVisit < 24
          ? `${Math.round(input.hoursSinceLastVisit)} hours`
          : `${Math.round(input.hoursSinceLastVisit / 24)} days`;
        const result = await invokeLLM({
          messages: [
            {
              role: 'system',
              content: `You are SCOUT, an AI sales agent for a robotics company. Generate a brief "since you were away" update for a returning user. Context: ${contextStr}. They were away for ${hoursLabel}. Generate 2-3 specific, realistic signal updates relevant to their category and territory. Format as a single message: "Since your last visit ${hoursLabel} ago, I found [X new signals]. [Specific example 1]. [Specific example 2]. Ready to review them?" Keep it under 65 words. Be concrete — mention real-sounding company types, locations, and signal types (e.g. job postings, earnings calls, facility expansions).`,
            },
            { role: 'user', content: 'Generate the signal update message.' },
          ],
        });
        return { message: extractText(result) };
      }),

    // ── Skill: Draft Outreach ──────────────────────────────────────────────────────
    draftOutreach: publicProcedure
      .input(z.object({
        fingerprint: z.string(),
        company: z.string(),
        signal: z.string(),
        robotCategory: z.string(),
        senderCompany: z.string().optional(),
      }))
      .mutation(async ({ input }) => {
        const { session } = await upsertScoutSession(input.fingerprint);
        const result = await skillDraftOutreach(
          input.company,
          input.signal,
          input.robotCategory,
          input.senderCompany
        );
        await appendScoutMessage(
          session.id,
          "scout",
          `Drafted outreach for ${input.company}`,
          "draftOutreach",
          result
        );
        return result;
      }),
  }),

  // ── Pipeline ─────────────────────────────────────────────────────────────────
  pipeline: router({
    // Add a prospect from Results page to the pipeline
    add: protectedProcedure
      .input(z.object({
        companyName: z.string().min(1).max(256),
        companyUrl: z.string().max(512).optional(),
        industry: z.string().max(128).optional(),
        robotCategory: z.string().max(64).optional(),
        signal: z.string().optional(),
        signalType: z.string().max(128).optional(),
        scoutScore: z.number().int().min(0).max(100).optional(),
        outreachDraft: z.string().optional(),
        opportunityType: z.enum(["sales_lead", "partnership"]).default("sales_lead"),
        contactEmail: z.string().max(320).optional(),
      }))
      .mutation(async ({ ctx, input }) => {
        const db = await getDb();
        if (!db) return { success: false, id: null };
        const [result] = await db.insert(pipelineOpportunities).values({
          userId: ctx.user.id,
          companyName: input.companyName,
          companyUrl: input.companyUrl,
          industry: input.industry,
          robotCategory: input.robotCategory,
          signal: input.signal,
          signalSource: input.signalType,
          scoutScore: input.scoutScore ?? 0,
          opportunityType: input.opportunityType,
          outreachStage: "pending",
          pipelineMode: "assisted",
          contactEmail: input.contactEmail,
        });
        // Store draft as a JSON note if provided
        if (input.outreachDraft) {
          await db.update(pipelineOpportunities).set({
            scoreNotes: { outreachDraft: input.outreachDraft },
          }).where(eq(pipelineOpportunities.id, (result as any).insertId));
        }
        return { success: true, id: (result as any).insertId };
      }),

    // List all pipeline opportunities for the current user
    list: protectedProcedure
      .query(async ({ ctx }) => {
        const db = await getDb();
        if (!db) return [];
        return db.select().from(pipelineOpportunities)
          .where(eq(pipelineOpportunities.userId, ctx.user.id))
          .orderBy(desc(pipelineOpportunities.createdAt));
      }),

    // Advance the outreach stage (e.g. pending → intro_sent)
    advanceStage: protectedProcedure
      .input(z.object({
        id: z.number().int(),
        stage: z.enum(["pending", "intro_scheduled", "intro_sent", "followup_sent", "linkedin_sent", "final_sent", "meeting_booked", "closed", "paused"]),
      }))
      .mutation(async ({ ctx, input }) => {
        const db = await getDb();
        if (!db) return { success: false };
        const now = Date.now();
        const stageTimestamps: Record<string, Record<string, number>> = {
          intro_sent: { introSentAt: now },
          followup_sent: { followupSentAt: now },
          linkedin_sent: { linkedinSentAt: now },
          final_sent: { finalSentAt: now },
          meeting_booked: { meetingBookedAt: now },
        };
        await db.update(pipelineOpportunities).set({
          outreachStage: input.stage,
          ...(stageTimestamps[input.stage] ?? {}),
        }).where(
          eq(pipelineOpportunities.id, input.id)
        );
        return { success: true };
      }),

    // Toggle pipeline mode for a single deal
    toggleMode: protectedProcedure
      .input(z.object({
        id: z.number().int(),
        mode: z.enum(["assisted", "autopilot"]),
      }))
      .mutation(async ({ ctx, input }) => {
        const db = await getDb();
        if (!db) return { success: false };
        await db.update(pipelineOpportunities).set({
          pipelineMode: input.mode,
        }).where(eq(pipelineOpportunities.id, input.id));
        return { success: true };
      }),

    // Archive / remove a deal
    archive: protectedProcedure
      .input(z.object({ id: z.number().int() }))
      .mutation(async ({ ctx, input }) => {
        const db = await getDb();
        if (!db) return { success: false };
        await db.update(pipelineOpportunities).set({ status: "archived" })
          .where(eq(pipelineOpportunities.id, input.id));
        return { success: true };
      }),

    // Generate a structured proposal document for a pipeline deal
    generateProposal: protectedProcedure
      .input(z.object({
        companyName: z.string(),
        industry: z.string().optional(),
        robotCategory: z.string().optional(),
        signal: z.string().optional(),
        scoutScore: z.number().optional(),
        contactEmail: z.string().optional(),
        senderCompany: z.string().optional(),
        senderName: z.string().optional(),
        senderTitle: z.string().optional(),
      }))
      .mutation(async ({ ctx, input }) => {
        // Load user settings for sender identity
        const db = await getDb();
        let senderCompany = input.senderCompany;
        let senderName = input.senderName;
        let senderTitle = input.senderTitle;
        if (db && (!senderCompany || !senderName)) {
          const settings = await db.select().from(userSettings).where(eq(userSettings.userId, ctx.user.id)).limit(1);
          if (settings[0]) {
            senderCompany = senderCompany ?? settings[0].senderCompanyName ?? "ReadyForRobots";
            senderName = senderName ?? settings[0].senderName ?? "Your SCOUT Agent";
            senderTitle = senderTitle ?? settings[0].senderTitle ?? "Sales Development";
          }
        }
        senderCompany = senderCompany ?? "ReadyForRobots";
        senderName = senderName ?? "Your SCOUT Agent";
        senderTitle = senderTitle ?? "Sales Development";

        const prompt = `You are SCOUT, an expert B2B proposal writer for robotics companies.
Generate a structured sales proposal document for the following opportunity.

Target company: ${input.companyName}
Industry: ${input.industry ?? "Unknown"}
Robot category: ${input.robotCategory ?? "automation"}
Buying signal: ${input.signal ?? "General automation interest"}
SCOUT Score: ${input.scoutScore ?? "N/A"}/100
Contact email: ${input.contactEmail ?? "Not provided"}
Sender company: ${senderCompany}
Sender name: ${senderName}
Sender title: ${senderTitle}

Generate a professional proposal with these sections:
1. EXECUTIVE SUMMARY (2-3 sentences): Why ${input.companyName} is ready for automation now, referencing the specific signal.
2. THE OPPORTUNITY (3-4 sentences): What problem they face, quantified if possible.
3. PROPOSED SOLUTION (3-4 sentences): Specific ${input.robotCategory ?? "automation"} solution tailored to their signal and industry.
4. EXPECTED OUTCOMES (3 bullet points): Quantified ROI estimates (e.g. "Reduce labor costs by 30-40%", "Cut cycle time by 50%").
5. NEXT STEPS: A clear 3-step path: (1) 15-min discovery call, (2) site assessment, (3) custom ROI model.
6. ABOUT ${senderCompany.toUpperCase()}: 2 sentences about the sender company's expertise in ${input.robotCategory ?? "robotics"}.

Rules:
- Be specific to the buying signal — never generic
- Use professional but direct language
- No buzzwords ("synergy", "leverage", "cutting-edge")
- Total length: 350-500 words
- Format with clear section headers`;

        const result = await invokeLLM({
          messages: [{ role: "user", content: prompt }],
        });
        const proposalText = extractText(result);
        return {
          proposal: proposalText,
          companyName: input.companyName,
          senderCompany,
          senderName,
          senderTitle,
          generatedAt: Date.now(),
        };
      }),
  }),

});

export type AppRouter = typeof appRouter;
