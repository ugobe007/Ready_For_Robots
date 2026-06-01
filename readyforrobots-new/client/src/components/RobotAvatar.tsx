import { useState } from "react";
import {
  resolveHumanoidLogo,
  resolveHumanoidLogoFallbackCdn,
  vendorHue,
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

const SIZE: Record<NonNullable<RobotAvatarProps["size"]>, { box: string; img: string; text: string }> = {
  sm: { box: "h-7 w-7", img: "h-4 w-4", text: "text-[9px]" },
  md: { box: "h-11 w-11", img: "h-7 w-7", text: "text-[11px]" },
  lg: { box: "h-14 w-14", img: "h-9 w-9", text: "text-xs" },
};

function InitialsFallback({ vendor, size }: { vendor: string; size: NonNullable<RobotAvatarProps["size"]> }) {
  const hue = vendorHue(vendor);
  const s = SIZE[size];
  return (
    <div
      className={`${s.box} flex shrink-0 items-center justify-center rounded-lg border border-white/10 ${s.text} font-bold text-white/85`}
      style={{
        background: `linear-gradient(135deg, hsl(${hue} 45% 28%) 0%, hsl(${(hue + 40) % 360} 35% 18%) 100%)`,
      }}
      aria-hidden
    >
      {vendorInitials(vendor)}
    </div>
  );
}

function LogoImage({
  meta,
  vendor,
  size,
  onError,
}: {
  meta: VendorLogoMeta;
  vendor: string;
  size: NonNullable<RobotAvatarProps["size"]>;
  onError: () => void;
}) {
  const s = SIZE[size];
  return (
    <div
      className={`${s.box} flex shrink-0 items-center justify-center rounded-lg border border-white/10`}
      style={{
        background: "linear-gradient(145deg, rgba(124,58,237,0.12) 0%, rgba(3,218,197,0.06) 100%)",
      }}
    >
      <img
        src={meta.src}
        alt=""
        loading="lazy"
        decoding="async"
        onError={onError}
        className={`${s.img} object-contain opacity-90`}
        style={{
          filter: meta.tinted ? undefined : "brightness(0) invert(1) opacity(0.82)",
        }}
      />
    </div>
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
      <div className={className}>
        <InitialsFallback vendor={vendor} size={size} />
      </div>
    );
  }

  const meta =
    stage === "cdn" ? resolveHumanoidLogoFallbackCdn(vendor) : primary;

  if (!meta) {
    return (
      <div className={className}>
        <InitialsFallback vendor={vendor} size={size} />
      </div>
    );
  }

  return (
    <div className={className}>
      <LogoImage
        meta={meta}
        vendor={vendor}
        size={size}
        onError={() => setStage(stage === "primary" ? "cdn" : "initials")}
      />
    </div>
  );
}
