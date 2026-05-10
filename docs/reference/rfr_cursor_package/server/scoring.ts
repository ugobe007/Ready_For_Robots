/**
 * SCOUT Score — 6-factor weighted lead qualification model.
 *
 * Tier 1 (Deal Quality, 60 pts total):
 *   1. Readiness to buy      — 25 pts  (timing signals, urgency)
 *   2. Well-defined use case — 20 pts  (clear automation fit)
 *   3. Achievable ROI        — 15 pts  (labor cost vs. robot cost math)
 *
 * Tier 2 (Deal Value, 40 pts total):
 *   4. Size of deployment    — 15 pts  (unit count, facility scale)
 *   5. Recognizable problem  — 15 pts  (known industry pain point)
 *   6. Customer value        — 10 pts  (brand recognition, company size)
 *
 * Total: 100 pts
 * Bands: 80–100 = Hot 🔴 | 60–79 = Warm 🟠 | 40–59 = Developing 🟡 | <40 = Monitoring ⚪
 */

export type ScoreInputs = {
  // Tier 1
  /** 0–25: signals indicating imminent purchase (job postings, CapEx, expansion) */
  readiness: number;
  /** 0–20: clarity of automation use case (warehouse pick, food processing, etc.) */
  useCase: number;
  /** 0–15: ROI achievability (labor cost savings vs. robot cost) */
  roi: number;
  // Tier 2
  /** 0–15: deployment scale (number of units, number of facilities) */
  deploymentSize: number;
  /** 0–15: how well-known the problem is in the industry */
  recognizableProblem: number;
  /** 0–10: brand value and company size of the prospect */
  customerValue: number;
};

export type ScoreResult = ScoreInputs & {
  /** Composite SCOUT Score 0–100 */
  total: number;
  /** Hot | Warm | Developing | Monitoring */
  band: "Hot" | "Warm" | "Developing" | "Monitoring";
  /** Hex color for the band */
  bandColor: string;
  /** Human-readable notes per factor */
  notes: Record<string, string>;
};

export const SCORE_WEIGHTS = {
  readiness: 25,
  useCase: 20,
  roi: 15,
  deploymentSize: 15,
  recognizableProblem: 15,
  customerValue: 10,
} as const;

export const SCORE_FACTORS: Array<{
  key: keyof ScoreInputs;
  label: string;
  maxScore: number;
  tier: 1 | 2;
  description: string;
}> = [
  {
    key: "readiness",
    label: "Readiness to Buy",
    maxScore: 25,
    tier: 1,
    description: "Timing signals: job postings, CapEx announcements, expansion plans, OSHA filings",
  },
  {
    key: "useCase",
    label: "Well-Defined Use Case",
    maxScore: 20,
    tier: 1,
    description: "Clarity of automation fit: warehouse pick, food processing, last-mile delivery, etc.",
  },
  {
    key: "roi",
    label: "Achievable ROI",
    maxScore: 15,
    tier: 1,
    description: "Labor cost savings vs. robot cost — is the math favorable within 24 months?",
  },
  {
    key: "deploymentSize",
    label: "Deployment Scale",
    maxScore: 15,
    tier: 2,
    description: "Number of units, facility count, and geographic spread of the deployment",
  },
  {
    key: "recognizableProblem",
    label: "Recognizable Problem",
    maxScore: 15,
    tier: 2,
    description: "Is this a well-known industry pain point with documented precedent?",
  },
  {
    key: "customerValue",
    label: "Customer Value",
    maxScore: 10,
    tier: 2,
    description: "Brand recognition, company size, and reference value of the prospect",
  },
];

/**
 * Clamp a score to [0, max].
 */
function clamp(value: number, max: number): number {
  return Math.max(0, Math.min(max, Math.round(value)));
}

/**
 * Compute the composite SCOUT Score from raw factor inputs.
 * Each factor input should be a 0–1 normalized value (e.g. 0.8 = 80% of max).
 */
export function scoreLead(inputs: ScoreInputs, notes?: Record<string, string>): ScoreResult {
  const clamped: ScoreInputs = {
    readiness: clamp(inputs.readiness, SCORE_WEIGHTS.readiness),
    useCase: clamp(inputs.useCase, SCORE_WEIGHTS.useCase),
    roi: clamp(inputs.roi, SCORE_WEIGHTS.roi),
    deploymentSize: clamp(inputs.deploymentSize, SCORE_WEIGHTS.deploymentSize),
    recognizableProblem: clamp(inputs.recognizableProblem, SCORE_WEIGHTS.recognizableProblem),
    customerValue: clamp(inputs.customerValue, SCORE_WEIGHTS.customerValue),
  };

  const total =
    clamped.readiness +
    clamped.useCase +
    clamped.roi +
    clamped.deploymentSize +
    clamped.recognizableProblem +
    clamped.customerValue;

  let band: ScoreResult["band"];
  let bandColor: string;

  if (total >= 80) {
    band = "Hot";
    bandColor = "#ef4444"; // red-500
  } else if (total >= 60) {
    band = "Warm";
    bandColor = "#FFB000"; // amber brand
  } else if (total >= 40) {
    band = "Developing";
    bandColor = "#a78bfa"; // purple brand
  } else {
    band = "Monitoring";
    bandColor = "rgba(255,255,255,0.35)";
  }

  return {
    ...clamped,
    total,
    band,
    bandColor,
    notes: notes ?? {},
  };
}

/**
 * Generate a SCOUT Score from a signal description using LLM-based inference.
 * Returns normalized factor scores (0–max for each factor).
 */
export async function scoreLeadFromSignal(params: {
  companyName: string;
  industry: string;
  robotCategory: string;
  signal: string;
  signalSource: string;
}): Promise<ScoreResult> {
  // Import here to avoid circular deps
  const { invokeLLM } = await import("./_core/llm");

  const prompt = `You are SCOUT, an AI sales qualification agent for robotics companies.

Analyze this sales opportunity and score it on 6 factors. Return ONLY valid JSON.

Company: ${params.companyName}
Industry: ${params.industry}
Robot Category: ${params.robotCategory}
Buying Signal: ${params.signal}
Signal Source: ${params.signalSource}

Score each factor as a number within its maximum range:
- readiness (0-25): How ready is this company to buy? Consider timing urgency.
- useCase (0-20): How well-defined is the automation use case?
- roi (0-15): How achievable is ROI within 24 months?
- deploymentSize (0-15): How large is the potential deployment?
- recognizableProblem (0-15): How well-known is this problem in the industry?
- customerValue (0-10): How valuable is this customer (brand, size, reference value)?

Also write a one-sentence note for each factor explaining the score.

Respond with this exact JSON structure:
{
  "readiness": <number>,
  "useCase": <number>,
  "roi": <number>,
  "deploymentSize": <number>,
  "recognizableProblem": <number>,
  "customerValue": <number>,
  "notes": {
    "readiness": "<one sentence>",
    "useCase": "<one sentence>",
    "roi": "<one sentence>",
    "deploymentSize": "<one sentence>",
    "recognizableProblem": "<one sentence>",
    "customerValue": "<one sentence>"
  }
}`;

  const response = await invokeLLM({
    messages: [
      { role: "system", content: "You are a sales qualification expert. Return only valid JSON." },
      { role: "user", content: prompt },
    ],
    response_format: {
      type: "json_schema",
      json_schema: {
        name: "scout_score",
        strict: true,
        schema: {
          type: "object",
          properties: {
            readiness: { type: "number" },
            useCase: { type: "number" },
            roi: { type: "number" },
            deploymentSize: { type: "number" },
            recognizableProblem: { type: "number" },
            customerValue: { type: "number" },
            notes: {
              type: "object",
              properties: {
                readiness: { type: "string" },
                useCase: { type: "string" },
                roi: { type: "string" },
                deploymentSize: { type: "string" },
                recognizableProblem: { type: "string" },
                customerValue: { type: "string" },
              },
              required: ["readiness", "useCase", "roi", "deploymentSize", "recognizableProblem", "customerValue"],
              additionalProperties: false,
            },
          },
          required: ["readiness", "useCase", "roi", "deploymentSize", "recognizableProblem", "customerValue", "notes"],
          additionalProperties: false,
        },
      },
    },
  });

  const raw = JSON.parse(response.choices[0].message.content as string);
  return scoreLead(
    {
      readiness: raw.readiness,
      useCase: raw.useCase,
      roi: raw.roi,
      deploymentSize: raw.deploymentSize,
      recognizableProblem: raw.recognizableProblem,
      customerValue: raw.customerValue,
    },
    raw.notes
  );
}
