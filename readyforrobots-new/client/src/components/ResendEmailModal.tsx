import React, { useState } from "react";
import { Mail, X, Check, Send, AlertCircle, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader } from "@/lib/supabase";
import { useAuth } from "@/contexts/AuthContext";

export interface ResendEmailModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultTo?: string;
  defaultSubject?: string;
  defaultBody?: string;
  companyName?: string;
  crmAccountId?: string;
  onSent?: (res: any) => void;
}

export function ResendEmailModal({
  isOpen,
  onClose,
  defaultTo = "",
  defaultSubject = "Robotic Labor Placement — ReadyForRobots",
  defaultBody = "",
  companyName,
  crmAccountId,
  onSent,
}: ResendEmailModalProps) {
  const { session } = useAuth();
  const [toEmail, setToEmail] = useState(defaultTo);
  const [subject, setSubject] = useState(defaultSubject);
  const [bodyText, setBodyText] = useState(defaultBody);
  const [cc, setCc] = useState("");
  const [showCc, setShowCc] = useState(false);
  const [sending, setSending] = useState(false);
  const [sentSuccess, setSentSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  // Sync state when props change
  React.useEffect(() => {
    if (isOpen) {
      setToEmail(defaultTo);
      setSubject(defaultSubject);
      setBodyText(defaultBody);
      setErrorMsg("");
      setSentSuccess(false);
    }
  }, [isOpen, defaultTo, defaultSubject, defaultBody]);

  if (!isOpen) return null;

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!toEmail.trim() || !toEmail.includes("@")) {
      setErrorMsg("Please enter a valid recipient email address.");
      return;
    }
    if (!subject.trim()) {
      setErrorMsg("Please enter a subject line.");
      return;
    }
    if (!bodyText.trim()) {
      setErrorMsg("Please enter the email body text.");
      return;
    }

    setSending(true);
    setErrorMsg("");

    try {
      const payload: Record<string, any> = {
        to_email: toEmail.trim(),
        subject: subject.trim(),
        body_text: bodyText.trim(),
        from_display_name: "Phelan",
        company_name: companyName,
        crm_account_id: crmAccountId,
      };

      if (cc.trim()) {
        payload.cc = cc
          .split(",")
          .map(s => s.trim())
          .filter(Boolean);
      }

      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };

      if (session?.access_token) {
        Object.assign(headers, authHeader(session.access_token));
      }

      const response = await fetch(
        `${getApiBase()}/api/crm/send-custom-email`,
        liveFetchInit({
          method: "POST",
          headers,
          body: JSON.stringify(payload),
        })
      );

      if (!response.ok) {
        const errText = await response.text();
        let detail = "Could not send email via Resend.";
        try {
          const parsed = JSON.parse(errText);
          detail = parsed.detail || detail;
        } catch {
          detail = errText || detail;
        }
        throw new Error(detail);
      }

      const data = await response.json();
      setSentSuccess(true);
      toast.success(`Email sent via Resend to ${toEmail}!`);
      if (onSent) onSent(data);

      setTimeout(() => {
        onClose();
        setSentSuccess(false);
      }, 1500);
    } catch (err) {
      const msg =
        err instanceof Error ? err.message : "Failed to send email via Resend.";
      setErrorMsg(msg);
      toast.error(msg);
    } finally {
      setSending(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl rounded-2xl border border-emerald-500/40 bg-slate-900 p-6 text-slate-100 shadow-2xl space-y-4"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              <Mail className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-extrabold text-white flex items-center gap-2">
                Send Email via Resend
                <span className="rounded-full bg-emerald-950 px-2 py-0.5 text-[10px] font-bold text-emerald-400 border border-emerald-800">
                  Resend API
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Phelan | Robot Job Analyst &bull;{" "}
                <span className="font-mono text-emerald-400">
                  readyforrobots.com
                </span>
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-white transition"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Error / Success Alerts */}
        {errorMsg && (
          <div className="flex items-center gap-2 rounded-xl border border-red-500/40 bg-red-950/50 p-3 text-xs text-red-300">
            <AlertCircle className="h-4 w-4 shrink-0 text-red-400" />
            <span>{errorMsg}</span>
          </div>
        )}

        {sentSuccess && (
          <div className="flex items-center gap-2 rounded-xl border border-emerald-500/50 bg-emerald-950/60 p-3 text-xs text-emerald-300 font-semibold">
            <Check className="h-4 w-4 text-emerald-400" />
            <span>
              Email successfully sent via Resend! Inbound replies route directly
              to your ReadyForRobots inbox.
            </span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSend} className="space-y-3">
          {/* Recipient */}
          <div>
            <div className="flex items-center justify-between">
              <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-400">
                Recipient Email (To) *
              </label>
              {!showCc && (
                <button
                  type="button"
                  onClick={() => setShowCc(true)}
                  className="text-[10px] font-semibold text-emerald-400 hover:underline"
                >
                  + Add CC
                </button>
              )}
            </div>
            <input
              type="email"
              required
              value={toEmail}
              onChange={e => setToEmail(e.target.value)}
              placeholder="executive@company.com"
              className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 font-mono"
            />
          </div>

          {/* CC */}
          {showCc && (
            <div>
              <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-400">
                CC (Comma Separated)
              </label>
              <input
                type="text"
                value={cc}
                onChange={e => setCc(e.target.value)}
                placeholder="colleague@company.com"
                className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-3.5 py-1.5 text-xs text-white placeholder-slate-500 focus:border-emerald-500 focus:outline-none font-mono"
              />
            </div>
          )}

          {/* Subject */}
          <div>
            <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Subject Line *
            </label>
            <input
              type="text"
              required
              value={subject}
              onChange={e => setSubject(e.target.value)}
              placeholder="Robotic Labor Placement"
              className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-3.5 py-2 text-xs font-semibold text-amber-300 placeholder-slate-500 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>

          {/* Body */}
          <div>
            <div className="flex items-center justify-between">
              <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-400">
                Email Body Text *
              </label>
              <span className="text-[10px] text-slate-400">
                Phelan Outreach Copy
              </span>
            </div>
            <textarea
              required
              rows={10}
              value={bodyText}
              onChange={e => setBodyText(e.target.value)}
              placeholder="Hi..."
              className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 p-3.5 text-xs leading-relaxed text-slate-200 placeholder-slate-500 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 font-mono resize-y"
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between pt-2">
            <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
              <Sparkles className="h-3.5 w-3.5 text-emerald-400" />
              <span>
                Sends directly via Resend — no external mail client needed.
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onClose}
                disabled={sending}
                className="rounded-xl border border-slate-700 bg-slate-800/80 px-4 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-700 hover:text-white transition disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={
                  sending ||
                  !toEmail.trim() ||
                  !subject.trim() ||
                  !bodyText.trim()
                }
                className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 border border-emerald-500 px-5 py-2 text-xs font-extrabold text-white hover:bg-emerald-500 transition shadow-lg shadow-emerald-950/50 disabled:opacity-50"
              >
                {sending ? (
                  <>
                    <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    <span>Sending via Resend...</span>
                  </>
                ) : (
                  <>
                    <Send className="h-3.5 w-3.5" />
                    <span>Send Email via Resend</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ResendEmailModal;
