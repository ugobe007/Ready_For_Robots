/**
 * Guard Supabase Auth magic-link sends.
 *
 * Built-in Supabase SMTP is a shared sender. Typos, disposable inboxes, and
 * login OTP that creates a new user on every miss are a bounce factory.
 * Cal/Resend outreach is a different pipe — this only covers Auth.
 */

const EMAIL_RE =
  /^[a-z0-9](?:[a-z0-9._%+\-]{0,62}[a-z0-9])?@[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?)+$/i;

const RESERVED_TLDS = new Set(["test", "invalid", "localhost", "example", "local", "internal"]);

const BLOCKED_DOMAINS = new Set([
  "example.com",
  "example.net",
  "example.org",
  "mailinator.com",
  "guerrillamail.com",
  "guerrillamailblock.com",
  "sharklasers.com",
  "grr.la",
  "10minutemail.com",
  "tempmail.com",
  "temp-mail.org",
  "throwaway.email",
  "yopmail.com",
  "trashmail.com",
  "discard.email",
  "getnada.com",
  "mailnesia.com",
  "maildrop.cc",
  "fakeinbox.com",
  "tempail.com",
  "emailondeck.com",
  "pokemail.net",
  "spam4.me",
]);

export function normalizeAuthEmail(raw: string): string | null {
  const text = (raw || "").trim().toLowerCase();
  if (!text || authEmailRejectReason(text)) return null;
  return text;
}

export function authEmailRejectReason(raw: string): string | null {
  const text = (raw || "").trim().toLowerCase();
  if (!text) return "Enter a work email.";
  if (text.includes(" ")) return "Email addresses cannot contain spaces.";
  if (!text.includes("@")) return "Use a full email like you@company.com.";
  if (text.includes("..")) return "That email has consecutive dots.";
  const [local, domain] = text.split("@");
  if (!local || !domain) return "Use a full email like you@company.com.";
  if (local.startsWith(".") || local.endsWith(".") || domain.startsWith(".") || domain.endsWith(".")) {
    return "That email is not a valid address.";
  }
  if (!EMAIL_RE.test(text)) {
    return "Enter a valid email (you@company.com).";
  }
  const labels = domain.split(".");
  const tld = labels[labels.length - 1] || "";
  if (tld.length < 2 || RESERVED_TLDS.has(tld)) {
    return "Use a real company email, not a test address.";
  }
  if (BLOCKED_DOMAINS.has(domain)) {
    return "Use a real work email. Disposable and example addresses bounce.";
  }
  return null;
}

export function otpNoAccountMessage(serverMessage: string): string {
  if (
    /signups? not allowed|user not found|unable to validate email address: invalid|error sending magic link/i.test(
      serverMessage,
    )
  ) {
    return "No account for that email yet. Create one on the signup page, or use Google / GitHub.";
  }
  return serverMessage;
}
