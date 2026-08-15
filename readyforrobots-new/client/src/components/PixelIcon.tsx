import type { PixelMap16 } from "@/lib/kareIcons";

type Props = {
  map: PixelMap16;
  /** CSS pixels per source pixel */
  scale?: number;
  fill?: string;
  background?: string;
  showGrid?: boolean;
  label?: string;
  className?: string;
};

/** Crisp nearest-neighbor render of a 16×16 Kare bitmap. */
export default function PixelIcon({
  map,
  scale = 16,
  fill = "#0a0a0a",
  background = "#ffffff",
  showGrid = false,
  label,
  className = "",
}: Props) {
  const size = 16 * scale;

  return (
    <div className={className}>
      {label ? (
        <p className="mb-2 font-mono text-[11px] uppercase tracking-[0.16em] text-slate-500">{label}</p>
      ) : null}
      <div
        role="img"
        aria-label={label || "pixel icon"}
        className="relative inline-block"
        style={{
          width: size,
          height: size,
          background,
          imageRendering: "pixelated",
          boxShadow: showGrid ? "inset 0 0 0 1px rgba(0,0,0,0.08)" : undefined,
        }}
      >
        <div
          className="grid h-full w-full"
          style={{
            gridTemplateColumns: `repeat(16, ${scale}px)`,
            gridTemplateRows: `repeat(16, ${scale}px)`,
          }}
        >
          {map.flatMap((row, y) =>
            row.map((bit, x) => (
              <span
                key={`${x}-${y}`}
                style={{
                  background: bit ? fill : "transparent",
                  boxShadow: showGrid ? "inset 0 0 0 0.5px rgba(100,100,100,0.25)" : undefined,
                }}
              />
            )),
          )}
        </div>
      </div>
    </div>
  );
}
