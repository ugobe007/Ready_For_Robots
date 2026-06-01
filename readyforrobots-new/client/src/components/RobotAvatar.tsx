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

const SIZE: Record<NonNullable<RobotAvatarProps["size"]>, { img: string; text: string }> = {
  sm: { img: "h-5 w-5", text: "text-[9px]" },
  md: { img: "h-9 w-9", text: "text-[10px]" },
  lg: { img: "h-11 w-11", text: "text-xs" },
};

function InitialsFallback({ vendor, size }: { vendor: string; size: NonNullable<RobotAvatarProps["size"]> }) {
  const s = SIZE[size];
  return (
    <span className={`${s.text} shrink-0 font-bold text-white/35`} aria-hidden>
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
    <img
      src={meta.src}
      alt=""
      loading="lazy"
      decoding="async"
      onError={onError}
      className={`${s.img} shrink-0 object-contain opacity-90`}
      style={{
        filter: meta.tinted ? undefined : "brightness(0) invert(1) opacity(0.82)",
      }}
    />
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
