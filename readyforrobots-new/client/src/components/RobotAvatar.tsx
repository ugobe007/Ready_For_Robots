import { useState } from "react";
import {
  resolveHumanoidLogo,
  resolveHumanoidLogoFallbackCdn,
  vendorInitials,
  type VendorLogoMeta,
} from "@/lib/humanoidVendorLogos";

type RobotAvatarProps = {
  vendor: string;
  name?: string;
  modelSlug?: string;
  productUrl?: string;
  imageUrl?: string | null;
  size?: "sm" | "md" | "lg";
  className?: string;
};

const SIZE: Record<
  NonNullable<RobotAvatarProps["size"]>,
  { img: string; text: string; glowScale: number }
> = {
  sm: { img: "h-5 w-5", text: "text-[9px]", glowScale: 1.85 },
  md: { img: "h-9 w-9", text: "text-[10px]", glowScale: 1.55 },
  lg: { img: "h-11 w-11", text: "text-xs", glowScale: 1.45 },
};

function LogoGlow({ size }: { size: NonNullable<RobotAvatarProps["size"]> }) {
  const { glowScale } = SIZE[size];
  return (
    <span
      className="pointer-events-none absolute inset-0 rounded-full"
      aria-hidden
      style={{
        transform: `scale(${glowScale})`,
        background:
          "radial-gradient(circle, rgba(167,139,250,0.28) 0%, rgba(3,218,197,0.12) 42%, transparent 72%)",
      }}
    />
  );
}

function InitialsFallback({ vendor, size }: { vendor: string; size: NonNullable<RobotAvatarProps["size"]> }) {
  const s = SIZE[size];
  return (
    <span
      className={`${s.text} relative shrink-0 font-bold text-white/40`}
      style={{ textShadow: "0 0 10px rgba(167,139,250,0.35), 0 0 18px rgba(3,218,197,0.12)" }}
      aria-hidden
    >
      {vendorInitials(vendor)}
    </span>
  );
}

function LogoImage({
  meta,
  size,
  onError,
}: {
  meta: VendorLogoMeta;
  size: NonNullable<RobotAvatarProps["size"]>;
  onError: () => void;
}) {
  const s = SIZE[size];
  return (
    <span className={`relative inline-flex shrink-0 items-center justify-center ${s.img}`}>
      <LogoGlow size={size} />
      <img
        src={meta.src}
        alt=""
        loading="lazy"
        decoding="async"
        onError={onError}
        className={`relative z-[1] h-full w-full object-contain opacity-90`}
        style={{
          filter: meta.tinted
            ? "drop-shadow(0 0 4px rgba(167,139,250,0.25))"
            : "brightness(0) invert(1) opacity(0.82) drop-shadow(0 0 4px rgba(167,139,250,0.2))",
        }}
      />
    </span>
  );
}

export default function RobotAvatar({
  vendor,
  modelSlug,
  productUrl,
  imageUrl,
  size = "md",
  className = "",
}: RobotAvatarProps) {
  const primary = resolveHumanoidLogo({ vendor, modelSlug, productUrl, imageUrl });
  const [stage, setStage] = useState<"primary" | "cdn" | "initials">("primary");

  if (stage === "initials") {
    return (
      <span className={`inline-flex items-center justify-center ${className}`}>
        <InitialsFallback vendor={vendor} size={size} />
      </span>
    );
  }

  const meta = stage === "cdn" ? resolveHumanoidLogoFallbackCdn(vendor) : primary;

  if (!meta) {
    return (
      <span className={`inline-flex items-center justify-center ${className}`}>
        <InitialsFallback vendor={vendor} size={size} />
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center justify-center ${className}`}>
      <LogoImage
        meta={meta}
        size={size}
        onError={() => setStage(stage === "primary" ? "cdn" : "initials")}
      />
    </span>
  );
}
