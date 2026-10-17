/**
 * Account created. Next step is the desk, or a robot URL.
 */
import { Link } from "wouter";
import { SiteFooter, SiteHeader } from "@/components/editorial";
import { useAuth } from "@/contexts/AuthContext";
import { readJobsHandoffSnapshot } from "@/lib/jobsHandoffSnapshot";

const SIGNUP_NAME_KEY = "rfr_signup_full_name";

export default function Welcome() {
  const { session } = useAuth();
  const user = session?.user;
  const meta = (user?.user_metadata ?? {}) as Record<string, unknown>;
  const stored =
    typeof window !== "undefined"
      ? window.localStorage.getItem(SIGNUP_NAME_KEY) || ""
      : "";
  const raw = String(meta.full_name || meta.name || stored || "").trim();
  const first = raw.split(/\s+/)[0] || "";
  const named = first && first.toLowerCase() !== "member" ? first : "";
  const saved = (readJobsHandoffSnapshot()?.jobs || []).filter(
    job => !job.is_example && (job.company_name || "").trim()
  );
  const fromFind = saved.length > 0;

  return (
    <div className="rfr-editorial rfr-account">
      <SiteHeader signedIn={Boolean(session)} />
      <main>
        <section className="rfr-account-stack">
          <div className="rfr-account-kicker">ACCOUNT CREATED</div>
          <h1>{named ? `You're in, ${named}.` : "You're in."}</h1>
          <p className="rfr-account-lede">
            {fromFind
              ? `Your ${saved.length} buyer${saved.length === 1 ? "" : "s"} are saved to your desk, and alerts are on for this robot.`
              : "Next, give us a robot. We'll find its buyers and keep watching for new ones."}
          </p>
          <div className="rfr-account-steps">
            <Link href="/desk">
              <span className="rfr-account-num">01</span>
              <strong>Open your desk →</strong>
              <span>
                {fromFind
                  ? `${saved.length} saved buyer${saved.length === 1 ? "" : "s"}, ready to work.`
                  : "Empty until you save a buyer. Start by adding a robot."}
              </span>
            </Link>
            <Link href="/?visit=jobs">
              <span className="rfr-account-num">02</span>
              <strong>Add another robot →</strong>
              <span>
                Paste a product page. Each robot gets its own buyers and its own alerts.
              </span>
            </Link>
          </div>
          <div className="rfr-account-note">
            <b>ALERTS ARE ON</b>
            <span>
              We'll email you when a new RFP or robotics hire matches one of your robots. Change this anytime in your account.
            </span>
          </div>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
