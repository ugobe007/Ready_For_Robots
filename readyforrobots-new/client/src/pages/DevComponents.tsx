import { useState, type CSSProperties } from "react";
import {
  ExampleBadge,
  Eyebrow,
  SignalRow,
  SiteFooter,
  SiteHeader,
  StatusChip,
  TierChip,
  TierLetter,
  UrlInput,
} from "@/components/editorial";

const sheet: CSSProperties = {
  maxWidth: 1296,
  margin: "0 auto",
  padding: "32px 24px 64px",
  display: "flex",
  flexDirection: "column",
  gap: 36,
};

function Caption({ children }: { children: string }) {
  return (
    <p
      style={{
        margin: "0 0 12px",
        fontFamily: "IBM Plex Mono, monospace",
        fontSize: 12,
        letterSpacing: "0.12em",
        textTransform: "uppercase",
        color: "#4A4F57",
      }}
    >
      {children}
    </p>
  );
}

export default function DevComponents() {
  const [url, setUrl] = useState("https://www.richtechrobotics.com/adam");

  return (
    <div className="rfr-editorial" style={{ minHeight: "100vh" }}>
      <SiteHeader />
      <div style={sheet}>
        <section>
          <Caption>Signed-in header</Caption>
          <SiteHeader signedIn initials="RC" />
        </section>
        <section>
          <Caption>Eyebrow</Caption>
          <Eyebrow label="Why now" aside="Sourced" />
        </section>
        <section>
          <Caption>Example badge</Caption>
          <ExampleBadge />
        </section>
        <section>
          <Caption>Tier letters</Caption>
          <div style={{ display: "flex", gap: 24, alignItems: "baseline" }}>
            <TierLetter tier="A" />
            <TierLetter tier="B" />
            <TierLetter tier="C" />
            <TierLetter tier="D" />
            <TierLetter tier="E" />
          </div>
        </section>
        <section>
          <Caption>Tier chips</Caption>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            <TierChip tier="A" label="RFP" />
            <TierChip tier="B" label="PILOT" />
            <TierChip tier="C" label="HIRING" />
            <TierChip tier="D" label="EXPANSION" />
            <TierChip tier="E" label="LABOR" />
          </div>
        </section>
        <section>
          <Caption>Signal rows</Caption>
          <SignalRow
            tier="A"
            label="RFP"
            title="Public RFP for beverage service robots"
            source="Company news"
          />
          <SignalRow
            tier="D"
            label="EXPANSION"
            title="New resort tower opening next year"
            source="Trade press"
          />
        </section>
        <section>
          <Caption>Status chips</Caption>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            <StatusChip status="exploring" />
            <StatusChip status="committed" />
            <StatusChip status="open" />
            <StatusChip status="unknown" />
          </div>
        </section>
        <section>
          <Caption>URL input</Caption>
          <UrlInput value={url} onChange={setUrl} />
        </section>
      </div>
      <SiteFooter />
    </div>
  );
}
