/**
 * Shared page shells — Precision Intelligence light theme.
 */
import Header from "@/components/Header";
import SiteFooter from "@/components/layout/SiteFooter";
import AdminNav from "@/components/AdminNav";

type PublicProps = {
  variant: "public";
  children: React.ReactNode;
  mainClassName?: string;
};

type WorkspaceProps = {
  variant: "workspace";
  children: React.ReactNode;
  adminNav?: boolean;
  wide?: boolean;
  mainClassName?: string;
};

type Props = PublicProps | WorkspaceProps;

export default function AppPageLayout(props: Props) {
  const mainPad = props.mainClassName ?? "pt-24 pb-16";

  if (props.variant === "public") {
    return (
      <div className="min-h-screen flex flex-col bg-slate-50 text-gray-900">
        <Header />
        <main className={`flex-1 ${mainPad}`}>{props.children}</main>
        <SiteFooter />
      </div>
    );
  }

  const containerClass = props.wide ? "container max-w-[1400px]" : "container";

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-gray-900">
      <Header />
      <main className={`flex-1 ${mainPad}`}>
        <div className={containerClass}>
          {props.adminNav && <AdminNav />}
          {props.children}
        </div>
      </main>
    </div>
  );
}
