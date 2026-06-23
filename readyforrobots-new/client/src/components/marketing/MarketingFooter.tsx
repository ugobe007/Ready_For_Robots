import SiteFooter from "@/components/layout/SiteFooter";

type Props = {
  newsletterEmail: string;
  newsletterStatus: "idle" | "submitting" | "success" | "error";
  onEmailChange: (v: string) => void;
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
};

/** Home newsletter footer — delegates to shared SiteFooter. */
export default function MarketingFooter({ newsletterEmail, newsletterStatus, onEmailChange, onSubmit }: Props) {
  return (
    <SiteFooter
      newsletterEmail={newsletterEmail}
      newsletterStatus={newsletterStatus}
      onEmailChange={onEmailChange}
      onNewsletterSubmit={onSubmit}
    />
  );
}
