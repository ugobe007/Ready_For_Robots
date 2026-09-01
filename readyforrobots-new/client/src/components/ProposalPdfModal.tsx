import { useEffect, useState } from "react";
import { Copy, Download, FileText, RefreshCw, X } from "lucide-react";
import { toast } from "sonner";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader } from "@/lib/supabase";

export type ProposalData = {
  proposal: string;
  company_name: string;
  sender_company: string;
  sender_name: string;
  sender_title: string;
  generated_at: number;
};

type ProposalPdfModalProps = {
  open: boolean;
  onClose: () => void;
  data: ProposalData | null;
  dealMeta?: {
    robotCategory?: string;
    signal?: string;
    scoutScore?: number;
  };
  accessToken: string;
};

async function fetchPdfBlob(
  token: string,
  data: ProposalData,
  proposalText: string,
  dealMeta?: ProposalPdfModalProps["dealMeta"]
): Promise<Blob> {
  const res = await fetch(`${getApiBase()}/api/proposals/pdf`, {
    ...liveFetchInit({
      method: "POST",
      headers: { ...authHeader(token), "Content-Type": "application/json" },
      body: JSON.stringify({
        company_name: data.company_name,
        proposal_text: proposalText,
        robot_category: dealMeta?.robotCategory,
        signal: dealMeta?.signal,
        scout_score: dealMeta?.scoutScore,
      }),
    }),
  });
  if (!res.ok) throw new Error("PDF generation failed");
  return res.blob();
}

export default function ProposalPdfModal({
  open,
  onClose,
  data,
  dealMeta,
  accessToken,
}: ProposalPdfModalProps) {
  const [editorText, setEditorText] = useState("");
  const [renderedText, setRenderedText] = useState("");
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!open || !data) return;
    const text = data.proposal;
    setEditorText(text);
    setRenderedText("");
    setLoading(true);
    setError(false);
    setBlobUrl(null);
    let cancelled = false;
    fetchPdfBlob(accessToken, data, text, dealMeta)
      .then(blob => {
        if (!cancelled) {
          setBlobUrl(URL.createObjectURL(blob));
          setRenderedText(text);
        }
      })
      .catch(() => {
        if (!cancelled) setError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [open, data, accessToken, dealMeta]);

  const handleClose = () => {
    if (blobUrl) URL.revokeObjectURL(blobUrl);
    setBlobUrl(null);
    onClose();
  };

  const handleUpdatePreview = async () => {
    if (!data) return;
    setUpdating(true);
    setError(false);
    try {
      const blob = await fetchPdfBlob(accessToken, data, editorText, dealMeta);
      if (blobUrl) URL.revokeObjectURL(blobUrl);
      setBlobUrl(URL.createObjectURL(blob));
      setRenderedText(editorText);
    } catch {
      toast.error("Failed to update preview");
    } finally {
      setUpdating(false);
    }
  };

  const handleDownload = async () => {
    if (!data) return;
    try {
      const blob = await fetchPdfBlob(
        accessToken,
        data,
        renderedText || editorText,
        dealMeta
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${data.company_name.replace(/[^a-z0-9]/gi, "-").toLowerCase()}-proposal.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Proposal PDF downloaded");
    } catch {
      toast.error("Failed to download PDF");
    }
  };

  if (!open || !data) return null;

  return (
    <div
      className="fixed inset-0 z-[70] flex flex-col"
      style={{ background: "#080415" }}
    >
      <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-amber-300" />
          <div>
            <p className="text-sm font-bold text-white">
              Proposal — {data.company_name}
            </p>
            <p className="text-[11px] text-white/40">
              Edit text, preview PDF, download
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={handleClose}
          className="rounded-lg p-2 text-white/40 hover:bg-white/5"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      <div className="flex flex-1 min-h-0 flex-col lg:flex-row">
        <div className="lg:w-1/2 border-b lg:border-b-0 lg:border-r border-white/10 p-4 flex flex-col gap-3">
          <textarea
            value={editorText}
            onChange={e => setEditorText(e.target.value)}
            className="flex-1 min-h-[240px] w-full rounded-xl border border-white/10 bg-white/[0.03] p-3 text-xs leading-relaxed text-white/80 font-mono resize-none"
            placeholder="Edit your proposal here…"
          />
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => void handleUpdatePreview()}
              disabled={updating}
              className="inline-flex items-center gap-1.5 rounded-lg border border-violet-400/30 bg-violet-500/15 px-3 py-2 text-xs font-bold text-violet-100 disabled:opacity-50"
            >
              {updating ? (
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <RefreshCw className="h-3.5 w-3.5" />
              )}
              Update preview
            </button>
            <button
              type="button"
              onClick={() => {
                void navigator.clipboard.writeText(editorText);
                toast.success("Copied to clipboard");
              }}
              className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-2 text-xs font-bold text-white/70"
            >
              <Copy className="h-3.5 w-3.5" />
              Copy
            </button>
            <button
              type="button"
              onClick={() => void handleDownload()}
              className="inline-flex items-center gap-1.5 rounded-lg border border-amber-400/35 bg-amber-500/15 px-3 py-2 text-xs font-bold text-amber-100"
            >
              <Download className="h-3.5 w-3.5" />
              Download PDF
            </button>
          </div>
        </div>

        <div className="lg:w-1/2 p-4 flex flex-col min-h-0">
          {loading ? (
            <div className="flex flex-1 items-center justify-center text-sm text-white/40">
              Rendering PDF…
            </div>
          ) : error ? (
            <div className="flex flex-1 items-center justify-center text-sm text-red-300">
              PDF preview failed
            </div>
          ) : blobUrl ? (
            <iframe
              title="Proposal PDF preview"
              src={blobUrl}
              className="flex-1 w-full rounded-xl border border-white/10 bg-white"
            />
          ) : null}
        </div>
      </div>
    </div>
  );
}
