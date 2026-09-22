import { useAuth } from "@/contexts/AuthContext";
import { isPaidSubscriber } from "@/hooks/useIsPaidUser";
import { Lock } from "lucide-react";
import { Link } from "wouter";

type LeadEmailDisplayProps = {
  email?: string | null;
  fallbackText?: string;
  isPaid?: boolean;
  className?: string;
  showUpgradeBtn?: boolean;
  variant?: "inline" | "table" | "input";
  onEmailChange?: (newEmail: string) => void;
  placeholder?: string;
};

export function maskEmail(email: string): string {
  if (!email || !email.includes("@")) return "buyer@vault.protected";
  const [local, domain] = email.split("@");
  const maskedLocal =
    local.length <= 2
      ? local[0] + "***"
      : local.slice(0, 2) + "***" + local.slice(-1);
  const domainParts = domain.split(".");
  const maskedDomain =
    domainParts[0].length <= 2
      ? domainParts[0][0] + "***"
      : domainParts[0].slice(0, 2) + "***";
  const tld = domainParts.slice(1).join(".");
  return `${maskedLocal}@${maskedDomain}.${tld}`;
}

export default function LeadEmailDisplay({
  email,
  fallbackText = "—",
  isPaid,
  className = "",
  showUpgradeBtn = false,
  variant = "inline",
  onEmailChange,
  placeholder = "buyer@example.com",
}: LeadEmailDisplayProps) {
  const { session } = useAuth();
  const paid = isPaidSubscriber(session, isPaid);

  if (variant === "input") {
    if (paid) {
      return (
        <input
          value={email || ""}
          onChange={onEmailChange ? e => onEmailChange(e.target.value) : undefined}
          placeholder={placeholder}
          className={`sb-input w-full ${className}`}
        />
      );
    }
    const maskedInputText = email ? maskEmail(email) : "buyer@vault.protected";
    return (
      <div className="relative flex items-center w-full">
        <input
          type="text"
          readOnly
          value={`${maskedInputText} (Vault Protected)`}
          className="sb-input w-full pr-28 cursor-not-allowed opacity-80 filter blur-[1.5px] select-none text-purple-300 font-mono"
        />
        <Link
          href="/pricing"
          className="absolute right-1.5 top-1/2 -translate-y-1/2 inline-flex items-center gap-1 rounded bg-purple-600 px-2.5 py-1 text-[10px] font-bold text-white shadow hover:bg-purple-500 transition-all font-sans cursor-pointer"
        >
          <Lock className="h-3 w-3" />
          <span>Unlock Email</span>
        </Link>
      </div>
    );
  }

  if (!email) {
    return <span className={`text-slate-500 ${className}`}>{fallbackText}</span>;
  }

  if (paid) {
    return <span className={className}>{email}</span>;
  }

  const masked = maskEmail(email);

  return (
    <span className={`inline-flex items-center gap-1.5 ${className}`}>
      <span
        className="filter blur-[3.5px] select-none text-purple-300 font-mono"
        title="Vault Contact Protection — Paid Plan Required ($19.99/mo)"
      >
        {masked}
      </span>
      <span className="inline-flex items-center gap-0.5 rounded bg-purple-500/20 px-1.5 py-0.5 text-[9px] font-mono font-semibold text-purple-300 border border-purple-500/30">
        <Lock className="h-2.5 w-2.5" /> Vault
      </span>
      {showUpgradeBtn && (
        <Link
          href="/pricing"
          className="inline-flex items-center gap-0.5 font-mono text-[10px] font-bold text-amber-300 hover:underline cursor-pointer"
        >
          Upgrade ($19.99/mo)
        </Link>
      )}
    </span>
  );
}
