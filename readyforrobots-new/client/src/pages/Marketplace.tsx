import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { Link } from "wouter";
import { ArrowRight, BriefcaseBusiness, FileText, Link2, Upload, Users } from "lucide-react";
import AdminNav from "@/components/AdminNav";
import Header from "@/components/Header";
import { useAuth } from "@/contexts/AuthContext";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader, supabase } from "@/lib/supabase";
import { toast } from "sonner";

type MarketplaceOrg = {
  team?: { id: string; name: string };
  profile?: {
    organizationType?: "vendor" | "buyer" | "admin";
    displayName?: string | null;
    website?: string | null;
    description?: string | null;
  };
};

type MarketplaceAsset = {
  id: string;
  filename: string;
  assetType: string;
  visibility: string;
  mimeType?: string | null;
  storagePath?: string | null;
  createdAt?: string | null;
};

type RfqRow = {
  id: string;
  title: string;
  status: string;
  dueAt?: string | null;
  projectDescription?: string | null;
};

type CommercialDocument = {
  id: string;
  documentType: string;
  status: string;
  title?: string | null;
  documentNumber?: string | null;
  amount?: number | null;
  currency?: string;
};

type IntegrationConnection = {
  id: string;
  connectionType: string;
  name: string;
  status: string;
  mcpServerUrl?: string | null;
  secretRef?: string | null;
};

const cardClass = "rounded-2xl border border-gray-200 bg-white p-5";

const marketplaceTeaserFeatures = [
  {
    icon: Users,
    title: "Buyer & vendor profiles",
    desc: "Publish your organization, decision makers, and procurement workflow so SIGNAL can route the right documents to the right team.",
    preview: [
      { label: "Buy-side", value: "Regional hospital system · warehouse AMR rollout" },
      { label: "Vendor", value: "Mobile robot OEM · logistics deployments" },
    ],
  },
  {
    icon: FileText,
    title: "RFP builder",
    desc: "Draft structured RFPs with technical requirements, evaluation criteria, and proposal deadlines — not just a PDF in email.",
    preview: [
      { label: "Open RFP", value: "Autonomous pallet transport · due Apr 18" },
      { label: "Requirements", value: "12 technical · 4 compliance · ROI model" },
    ],
  },
  {
    icon: Upload,
    title: "Vendor materials",
    desc: "Upload decks, product specs, case studies, pricing sheets, and compliance docs in one shared workspace.",
    preview: [
      { label: "Assets", value: "product_spec · case_study · pricing · compliance" },
      { label: "Visibility", value: "Private to buyer team until proposal stage" },
    ],
  },
  {
    icon: BriefcaseBusiness,
    title: "Quotes, invoices & POs",
    desc: "Track official commercial documents from draft quote through signed PO — linked to the RFP and supporting assets.",
    preview: [
      { label: "Quote", value: "Q-2026-0412 · $284,000 · pending review" },
      { label: "PO", value: "PO milestone scheduled after technical sign-off" },
    ],
  },
  {
    icon: Link2,
    title: "MCP & API connections",
    desc: "Connect ERP, quoting, and procurement systems via scoped MCP servers — credentials stay in your secret manager.",
    preview: [
      { label: "Scopes", value: "rfqs:read · quotes:create · invoices:read" },
      { label: "Guardrail", value: "Secret references only — no raw API keys stored" },
    ],
  },
];
const inputClass = "w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-900 outline-none placeholder:text-gray-400";
const labelClass = "mb-1 block text-[10px] uppercase tracking-widest text-gray-400";

function splitLines(value: string) {
  return value.split("\n").map((x) => x.trim()).filter(Boolean);
}

function tryJson(value: string, fallback: unknown) {
  if (!value.trim()) return fallback;
  try {
    return JSON.parse(value);
  } catch {
    return fallback;
  }
}

export default function Marketplace() {
  const { session, loading } = useAuth();
  const [org, setOrg] = useState<MarketplaceOrg | null>(null);
  const [assets, setAssets] = useState<MarketplaceAsset[]>([]);
  const [rfqs, setRfqs] = useState<RfqRow[]>([]);
  const [documents, setDocuments] = useState<CommercialDocument[]>([]);
  const [connections, setConnections] = useState<IntegrationConnection[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  const [orgForm, setOrgForm] = useState({
    organization_type: "buyer" as "buyer" | "vendor",
    display_name: "",
    website: "",
    description: "",
    decision_makers: "[]",
    procurement_workflow: "{}",
    po_preferences: "{}",
  });
  const [assetForm, setAssetForm] = useState({ asset_type: "deck", visibility: "private" });
  const [assetFile, setAssetFile] = useState<File | null>(null);
  const [rfqForm, setRfqForm] = useState({
    title: "",
    summary: "",
    project_description: "",
    timeline_summary: "",
    automation_category: "",
    due_at: "",
    requirements: "",
    technical_specs: "{}",
    decision_makers: "[]",
    schedule: "[]",
  });
  const [docForm, setDocForm] = useState({
    document_type: "quote",
    title: "",
    document_number: "",
    amount: "",
    due_at: "",
  });
  const [connectionForm, setConnectionForm] = useState({
    connection_type: "mcp_server",
    name: "",
    mcp_server_url: "https://ready-2-robot.fly.dev/mcp/",
    base_url: "",
    auth_type: "api_key",
    secret_ref: "",
    allowed_scopes: "quotes:create\ninvoices:read\nrfqs:read",
  });

  const authFetch = useCallback(
    async (path: string, init: RequestInit = {}) => {
      const token = session?.access_token;
      if (!token) throw new Error("Not signed in");
      const response = await fetch(
        `${getApiBase()}${path}`,
        liveFetchInit({ ...init, headers: { ...authHeader(token), ...init.headers } }),
      );
      const text = await response.text();
      if (!response.ok) throw new Error(text || response.statusText);
      return text ? JSON.parse(text) : null;
    },
    [session?.access_token],
  );

  const loadWorkspace = useCallback(async () => {
    if (!session?.access_token) return;
    setBusy(true);
    setMessage("");
    try {
      const [orgData, assetData, rfqData, docData, connectionData] = await Promise.all([
        authFetch("/api/marketplace/organization"),
        authFetch("/api/marketplace/assets"),
        authFetch("/api/marketplace/rfqs?include_drafts=true"),
        authFetch("/api/marketplace/commercial-documents"),
        authFetch("/api/marketplace/connections"),
      ]);
      setOrg(orgData);
      setAssets(assetData.assets || []);
      setRfqs(rfqData.rfqs || []);
      setDocuments(docData.documents || []);
      setConnections(connectionData.connections || []);
      setOrgForm((current) => ({
        ...current,
        organization_type: orgData.profile?.organizationType || current.organization_type,
        display_name: orgData.profile?.displayName || "",
        website: orgData.profile?.website || "",
        description: orgData.profile?.description || "",
      }));
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Could not load marketplace workspace");
    } finally {
      setBusy(false);
    }
  }, [authFetch, session?.access_token]);

  useEffect(() => {
    void loadWorkspace();
  }, [loadWorkspace]);

  const saveOrganization = async () => {
    setBusy(true);
    try {
      await authFetch("/api/marketplace/organization", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          organization_type: orgForm.organization_type,
          display_name: orgForm.display_name,
          website: orgForm.website,
          description: orgForm.description,
          decision_makers: tryJson(orgForm.decision_makers, []),
          procurement_workflow: tryJson(orgForm.procurement_workflow, {}),
          po_preferences: tryJson(orgForm.po_preferences, {}),
        }),
      });
      toast.success("Marketplace profile saved.");
      await loadWorkspace();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not save profile");
    } finally {
      setBusy(false);
    }
  };

  const uploadAsset = async () => {
    if (!assetFile || !session?.access_token) {
      toast.error("Choose a file first.");
      return;
    }
    const data = new FormData();
    data.append("asset_type", assetForm.asset_type);
    data.append("visibility", assetForm.visibility);
    data.append("metadata", JSON.stringify({ source: "marketplace_ui" }));
    data.append("file", assetFile);
    setBusy(true);
    try {
      const response = await fetch(
        `${getApiBase()}/api/marketplace/assets/upload`,
        liveFetchInit({ method: "POST", headers: { ...authHeader(session.access_token) }, body: data }),
      );
      if (!response.ok) throw new Error(await response.text());
      setAssetFile(null);
      toast.success("Asset uploaded.");
      await loadWorkspace();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not upload asset");
    } finally {
      setBusy(false);
    }
  };

  const createRfq = async () => {
    setBusy(true);
    try {
      await authFetch("/api/marketplace/rfqs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: rfqForm.title,
          summary: rfqForm.summary,
          project_description: rfqForm.project_description,
          timeline_summary: rfqForm.timeline_summary,
          automation_category: rfqForm.automation_category,
          status: "draft",
          due_at: rfqForm.due_at ? new Date(rfqForm.due_at).toISOString() : null,
          decision_makers: tryJson(rfqForm.decision_makers, []),
          technical_specs: tryJson(rfqForm.technical_specs, {}),
          workflow_process: { process: "buyer-defined", notes: rfqForm.timeline_summary },
          schedule: tryJson(rfqForm.schedule, []),
          evaluation_criteria: ["technical fit", "timeline", "ROI", "service coverage"],
          requirements: splitLines(rfqForm.requirements).map((body) => ({ requirement_type: "technical", body, priority: "required" })),
        }),
      });
      toast.success("Draft RFP created.");
      setRfqForm((current) => ({ ...current, title: "", summary: "", project_description: "", requirements: "" }));
      await loadWorkspace();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not create RFP");
    } finally {
      setBusy(false);
    }
  };

  const createScheduleEvent = async (rfq: RfqRow) => {
    if (!rfq.dueAt) {
      toast.error("Add an RFP due date first.");
      return;
    }
    try {
      await authFetch(`/api/marketplace/rfqs/${rfq.id}/schedule`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_type: "proposal_deadline",
          title: `Proposal deadline: ${rfq.title}`,
          due_at: rfq.dueAt,
          reminder_offsets: [14, 7, 2],
          email_recipients: [],
          payload: { source: "marketplace_ui" },
        }),
      });
      toast.success("RFP schedule event created.");
      await loadWorkspace();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not schedule RFP event");
    }
  };

  const createCommercialDocument = async () => {
    if (!org?.team?.id) return;
    setBusy(true);
    try {
      await authFetch("/api/marketplace/commercial-documents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          buyer_team_id: org.team.id,
          vendor_team_id: org.team.id,
          document_type: docForm.document_type,
          status: "draft",
          document_number: docForm.document_number,
          title: docForm.title,
          amount: docForm.amount ? Number(docForm.amount) : null,
          due_at: docForm.due_at ? new Date(docForm.due_at).toISOString() : null,
          asset_ids: assets.slice(0, 3).map((asset) => asset.id),
          payload: { note: "Created from marketplace console" },
        }),
      });
      toast.success("Commercial document created.");
      await loadWorkspace();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not create document");
    } finally {
      setBusy(false);
    }
  };

  const createConnection = async () => {
    setBusy(true);
    try {
      await authFetch("/api/marketplace/connections", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          connection_type: connectionForm.connection_type,
          name: connectionForm.name,
          status: "draft",
          base_url: connectionForm.base_url,
          mcp_server_url: connectionForm.mcp_server_url,
          auth_type: connectionForm.auth_type,
          secret_ref: connectionForm.secret_ref,
          allowed_scopes: splitLines(connectionForm.allowed_scopes),
          config: { guardrail: "No raw credentials stored in Ready For Robots" },
        }),
      });
      toast.success("Connection reference created.");
      await loadWorkspace();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not create connection");
    } finally {
      setBusy(false);
    }
  };

  const issuePartnerApiKey = async (connectionId: string, connectionName: string) => {
    setBusy(true);
    try {
      const out = await authFetch(`/api/marketplace/connections/${connectionId}/api-keys`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: `${connectionName} MCP key` }),
      });
      toast.success("Partner API key created — copy it now; it won't be shown again.");
      if (out?.apiKey) {
        window.prompt("Copy this partner API key:", out.apiKey);
      }
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not issue API key");
    } finally {
      setBusy(false);
    }
  };

  if (!supabase) {
    return <ShellMessage message="Supabase is not configured in this build." />;
  }
  if (loading) {
    return <ShellMessage message="Loading marketplace workspace..." />;
  }
  if (!session) {
    return <MarketplaceTeaser />;
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Header />
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 pb-12 pt-24">
        <AdminNav />
        <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: "#FFB000" }}>
          Marketplace workspace
        </p>
        <h1 className="text-2xl font-black text-gray-900" style={{ fontFamily: "'Sora', system-ui" }}>
          Profiles, RFPs, proposals, quotes, invoices, and connections
        </h1>
        <p className="mt-2 max-w-3xl text-sm leading-relaxed text-gray-500">
          Build the buy-side RFP workflow and the vendor-side document exchange. SIGNAL can use this context to route official proposals, specs, quotes, invoices, and PO milestones between both sides of the marketplace.
        </p>
        {message && <p className="mt-4 rounded-lg border border-red-500/30 p-3 text-sm text-red-200">{message}</p>}
        {busy && <p className="mt-4 text-xs text-gray-400">Working...</p>}

        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <section className={cardClass}>
            <SectionTitle title="Organization Profile" kicker={org?.team?.name || "Workspace"} />
            <div className="grid gap-3">
              <select value={orgForm.organization_type} onChange={(e) => setOrgForm((s) => ({ ...s, organization_type: e.target.value as "buyer" | "vendor" }))} className={inputClass}>
                <option value="buyer">Buy-side customer</option>
                <option value="vendor">Robot company</option>
              </select>
              <Input label="Display name" value={orgForm.display_name} onChange={(display_name) => setOrgForm((s) => ({ ...s, display_name }))} />
              <Input label="Website" value={orgForm.website} onChange={(website) => setOrgForm((s) => ({ ...s, website }))} />
              <Textarea label="Description" value={orgForm.description} rows={3} onChange={(description) => setOrgForm((s) => ({ ...s, description }))} />
              <Textarea label="Decision makers JSON" value={orgForm.decision_makers} rows={3} onChange={(decision_makers) => setOrgForm((s) => ({ ...s, decision_makers }))} />
              <button onClick={() => void saveOrganization()} className="rounded-lg border border-amber-400 bg-amber-400 px-3 py-2 text-xs font-bold text-[#111827]">Save profile</button>
            </div>
          </section>

          <section className={cardClass}>
            <SectionTitle title="Upload Materials" kicker={`${assets.length} assets`} />
            <div className="grid gap-3">
              <select value={assetForm.asset_type} onChange={(e) => setAssetForm((s) => ({ ...s, asset_type: e.target.value }))} className={inputClass}>
                {["deck", "product_spec", "case_study", "pricing", "compliance", "proposal", "other"].map((value) => <option key={value} value={value}>{value}</option>)}
              </select>
              <input type="file" onChange={(e) => setAssetFile(e.target.files?.[0] || null)} className="text-sm text-gray-500" />
              <button onClick={() => void uploadAsset()} className="rounded-lg border border-gray-200 bg-white/[0.05] px-3 py-2 text-xs font-bold text-gray-700">Upload asset</button>
              <ListEmpty items={assets} empty="No assets uploaded yet." render={(asset) => `${asset.assetType}: ${asset.filename}`} />
            </div>
          </section>

          <section className={cardClass}>
            <SectionTitle title="Buyer RFP Builder" kicker={`${rfqs.length} RFPs`} />
            <div className="grid gap-3">
              <Input label="RFP title" value={rfqForm.title} onChange={(title) => setRfqForm((s) => ({ ...s, title }))} />
              <Textarea label="Project description" value={rfqForm.project_description} rows={4} onChange={(project_description) => setRfqForm((s) => ({ ...s, project_description }))} />
              <Textarea label="Technical requirements, one per line" value={rfqForm.requirements} rows={4} onChange={(requirements) => setRfqForm((s) => ({ ...s, requirements }))} />
              <Input label="Due date/time" type="datetime-local" value={rfqForm.due_at} onChange={(due_at) => setRfqForm((s) => ({ ...s, due_at }))} />
              <Textarea label="Technical specs JSON" value={rfqForm.technical_specs} rows={3} onChange={(technical_specs) => setRfqForm((s) => ({ ...s, technical_specs }))} />
              <button onClick={() => void createRfq()} className="rounded-lg border border-amber-400 bg-amber-400 px-3 py-2 text-xs font-bold text-[#111827]">Create draft RFP</button>
              <ListEmpty
                items={rfqs}
                empty="No RFPs yet."
                render={(rfq) => `${rfq.status}: ${rfq.title}`}
                action={(rfq) => <button onClick={() => void createScheduleEvent(rfq)} className="text-[10px] font-bold text-amber-300 underline">Schedule deadline</button>}
              />
            </div>
          </section>

          <section className={cardClass}>
            <SectionTitle title="Quotes, Invoices, POs" kicker={`${documents.length} documents`} />
            <div className="grid gap-3">
              <select value={docForm.document_type} onChange={(e) => setDocForm((s) => ({ ...s, document_type: e.target.value }))} className={inputClass}>
                {["proposal", "quote", "invoice", "purchase_order"].map((value) => <option key={value} value={value}>{value}</option>)}
              </select>
              <Input label="Document title" value={docForm.title} onChange={(title) => setDocForm((s) => ({ ...s, title }))} />
              <Input label="Document number" value={docForm.document_number} onChange={(document_number) => setDocForm((s) => ({ ...s, document_number }))} />
              <Input label="Amount" value={docForm.amount} onChange={(amount) => setDocForm((s) => ({ ...s, amount }))} />
              <button onClick={() => void createCommercialDocument()} className="rounded-lg border border-gray-200 bg-white/[0.05] px-3 py-2 text-xs font-bold text-gray-700">Create document</button>
              <ListEmpty items={documents} empty="No commercial documents yet." render={(doc) => `${doc.documentType}: ${doc.title || doc.documentNumber || doc.status}`} />
            </div>
          </section>

          <section className={`${cardClass} lg:col-span-2`}>
            <SectionTitle title="MCP / API Connections" kicker={`${connections.length} connections`} />
            <div className="grid gap-3 md:grid-cols-2">
              <Input label="Connection name" value={connectionForm.name} onChange={(name) => setConnectionForm((s) => ({ ...s, name }))} />
              <Input label="MCP server URL" value={connectionForm.mcp_server_url} onChange={(mcp_server_url) => setConnectionForm((s) => ({ ...s, mcp_server_url }))} />
              <Input label="API base URL" value={connectionForm.base_url} onChange={(base_url) => setConnectionForm((s) => ({ ...s, base_url }))} />
              <Input label="Secret reference" value={connectionForm.secret_ref} onChange={(secret_ref) => setConnectionForm((s) => ({ ...s, secret_ref }))} />
              <Textarea label="Allowed scopes, one per line" value={connectionForm.allowed_scopes} rows={4} onChange={(allowed_scopes) => setConnectionForm((s) => ({ ...s, allowed_scopes }))} />
              <div className="rounded-xl border border-gray-100 bg-black/10 p-3 text-xs text-white/42">
                Store credentials in your secret manager, then paste only a reference here. Ready For Robots stores `secret_ref`, connection URLs, scopes, and config, not raw API keys.
              </div>
            </div>
            <button onClick={() => void createConnection()} className="mt-3 rounded-lg border border-amber-400/35 bg-amber-400/10 px-3 py-2 text-xs font-bold text-amber-100">Create connection reference</button>
            <div className="mt-3 space-y-2">
              <ListEmpty items={connections} empty="No connections yet." render={(connection) => `${connection.connectionType}: ${connection.name} (${connection.status})`} />
              {connections.map((connection) => (
                <button
                  key={connection.id}
                  type="button"
                  onClick={() => void issuePartnerApiKey(connection.id, connection.name)}
                  className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-[11px] font-bold text-gray-600"
                >
                  Issue MCP API key for {connection.name}
                </button>
              ))}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

function MarketplaceTeaser() {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Header />
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 pb-16 pt-24">
        <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: "#FFB000" }}>
          Robot automation marketplace
        </p>
        <h1 className="max-w-3xl text-3xl font-black text-gray-900 sm:text-4xl" style={{ fontFamily: "'Sora', system-ui" }}>
          RFPs, proposals, quotes, and procurement — in one workspace
        </h1>
        <p className="mt-4 max-w-3xl text-sm leading-relaxed text-gray-500">
          Ready For Robots connects buy-side automation teams with robot vendors through structured RFPs, shared materials,
          and official commercial documents. SIGNAL uses this context to route proposals, specs, and PO milestones between both sides.
        </p>

        <div className="mt-8 grid gap-4 lg:grid-cols-2">
          {marketplaceTeaserFeatures.map((feature) => {
            const Icon = feature.icon;
            return (
              <section key={feature.title} className={cardClass}>
                <div className="mb-4 flex items-start gap-3">
                  <div
                    className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl"
                    style={{ color: "#059669", background: "rgba(3,218,197,0.08)", border: "1px solid rgba(3,218,197,0.2)" }}
                  >
                    <Icon className="h-4 w-4" />
                  </div>
                  <div>
                    <h2 className="text-lg font-black text-gray-900">{feature.title}</h2>
                    <p className="mt-1 text-sm leading-relaxed text-white/42">{feature.desc}</p>
                  </div>
                </div>
                <div className="grid gap-2">
                  {feature.preview.map((row) => (
                    <div key={row.label} className="rounded-xl border border-gray-100 bg-black/10 px-3 py-2.5">
                      <p className="text-[10px] font-bold uppercase tracking-widest text-white/28">{row.label}</p>
                      <p className="mt-1 text-xs text-gray-500">{row.value}</p>
                    </div>
                  ))}
                </div>
              </section>
            );
          })}
        </div>

        <section className={`${cardClass} mt-4 border-amber-400/25 bg-amber-400/[0.04]`}>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-bold text-gray-900">Ready to publish an RFP or respond as a vendor?</p>
              <p className="mt-1 text-xs text-gray-500">
                Create a free account to save profiles, upload materials, and manage official documents.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link
                href="/signup?next=/marketplace"
                className="inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-bold"
                style={{ color: "#111827", background: "#FFB000" }}
              >
                Create account <ArrowRight className="h-3.5 w-3.5" />
              </Link>
              <Link
                href="/login?next=/marketplace"
                className="inline-flex items-center rounded-xl border border-gray-200 px-4 py-2.5 text-xs font-bold text-gray-600"
              >
                Sign in
              </Link>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

function ShellMessage({ message }: { message: string }) {
  return (
    <div className="min-h-screen px-4 pt-24 text-center text-gray-500 bg-slate-50">
      <Header />
      {message}
    </div>
  );
}

function SectionTitle({ title, kicker }: { title: string; kicker: string }) {
  return (
    <div className="mb-4 flex items-center justify-between gap-3">
      <h2 className="text-lg font-black text-gray-900">{title}</h2>
      <span className="rounded-full border border-gray-200 px-2 py-1 text-[10px] font-bold text-gray-400">{kicker}</span>
    </div>
  );
}

function Input({ label, value, onChange, type = "text" }: { label: string; value: string; onChange: (value: string) => void; type?: string }) {
  return (
    <label className="block">
      <span className={labelClass}>{label}</span>
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)} className={inputClass} />
    </label>
  );
}

function Textarea({ label, value, onChange, rows }: { label: string; value: string; rows: number; onChange: (value: string) => void }) {
  return (
    <label className="block">
      <span className={labelClass}>{label}</span>
      <textarea value={value} rows={rows} onChange={(e) => onChange(e.target.value)} className={`${inputClass} leading-relaxed`} />
    </label>
  );
}

function ListEmpty<T>({ items, empty, render, action }: { items: T[]; empty: string; render: (item: T) => string; action?: (item: T) => ReactNode }) {
  if (!items.length) return <p className="rounded-xl border border-gray-100 bg-black/10 p-3 text-xs text-gray-400">{empty}</p>;
  return (
    <div className="grid gap-2">
      {items.slice(0, 5).map((item, index) => (
        <div key={index} className="flex items-center justify-between gap-3 rounded-xl border border-gray-100 bg-black/10 p-3 text-xs text-gray-500">
          <span className="truncate">{render(item)}</span>
          {action?.(item)}
        </div>
      ))}
    </div>
  );
}
