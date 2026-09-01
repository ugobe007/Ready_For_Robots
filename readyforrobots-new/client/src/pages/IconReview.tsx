/**
 * Local review board for Susan Kare–style RFR icons.
 * Visit: http://127.0.0.1:5173/icon-review
 * Face = 15×15 from branding/face-icon-reference.png
 */
import PixelIcon from "@/components/PixelIcon";
import {
  FACE_EMERALD,
  FACE_WHITE,
  KARE_FACE,
  KARE_GRIPPER,
} from "@/lib/kareIcons";

const SWATCHES = [
  { name: "Ink on paper", fill: "#0a0a0a", bg: "#ffffff" },
  { name: "Emerald on navy (dark bg)", fill: FACE_EMERALD, bg: "#081126" },
  { name: "White on navy (dark bg)", fill: FACE_WHITE, bg: "#081126" },
  { name: "White on emerald CTA", fill: FACE_WHITE, bg: "#059669" },
] as const;

export default function IconReview() {
  return (
    <div className="min-h-screen bg-[#0b1220] px-6 py-10 text-slate-100 sm:px-10">
      <div className="mx-auto max-w-5xl">
        <p className="font-mono text-[11px] uppercase tracking-[0.22em] text-[#3ecf8e]">
          ReadyForRobots · icon review
        </p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight text-white sm:text-3xl">
          Susan Kare 16×16 set
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
          Gripper = main mark (deployments / work). Face = Cal / live
          personality. Rendered nearest-neighbor from bitmaps — no blur.
        </p>

        <section className="mt-10">
          <h2 className="font-mono text-[11px] uppercase tracking-[0.18em] text-slate-500">
            Large (×16) with grid
          </h2>
          <div className="mt-4 flex flex-wrap gap-10">
            <PixelIcon
              map={KARE_GRIPPER}
              scale={16}
              showGrid
              label="4 · Robot hand (main)"
              fill="#0a0a0a"
              background="#f4f4f5"
            />
            <PixelIcon
              map={KARE_FACE}
              scale={16}
              showGrid
              label="Face (Cal / live)"
              fill="#0a0a0a"
              background="#f4f4f5"
            />
          </div>
        </section>

        <section className="mt-12">
          <h2 className="font-mono text-[11px] uppercase tracking-[0.18em] text-slate-500">
            Colorways on product navy
          </h2>
          <div className="mt-4 grid gap-8 sm:grid-cols-2">
            {SWATCHES.map(s => (
              <div
                key={s.name}
                className="rounded-lg border border-white/10 p-4"
              >
                <p className="mb-3 font-mono text-[11px] text-slate-500">
                  {s.name}
                </p>
                <div className="flex flex-wrap gap-6">
                  <PixelIcon
                    map={KARE_GRIPPER}
                    scale={8}
                    fill={s.fill}
                    background={s.bg}
                    label="gripper"
                  />
                  <PixelIcon
                    map={KARE_FACE}
                    scale={8}
                    fill={s.fill}
                    background={s.bg}
                    label="face"
                  />
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="mt-12">
          <h2 className="font-mono text-[11px] uppercase tracking-[0.18em] text-slate-500">
            Favicon sizes
          </h2>
          <div className="mt-4 flex flex-wrap items-end gap-8">
            {[1, 2, 3, 4].map(s => (
              <div key={s} className="text-center">
                <PixelIcon
                  map={KARE_GRIPPER}
                  scale={s}
                  fill="#f59e0b"
                  background="#07111f"
                />
                <p className="mt-2 font-mono text-[10px] text-slate-600">
                  {16 * s}px
                </p>
              </div>
            ))}
            {[1, 2, 3, 4].map(s => (
              <div key={`f-${s}`} className="text-center">
                <PixelIcon
                  map={KARE_FACE}
                  scale={s}
                  fill={FACE_EMERALD}
                  background="#07111f"
                />
                <p className="mt-2 font-mono text-[10px] text-slate-600">
                  face {15 * s}px
                </p>
              </div>
            ))}
            {[1, 2, 3, 4].map(s => (
              <div key={`fw-${s}`} className="text-center">
                <PixelIcon
                  map={KARE_FACE}
                  scale={s}
                  fill={FACE_WHITE}
                  background="#059669"
                />
                <p className="mt-2 font-mono text-[10px] text-slate-600">
                  white {15 * s}px
                </p>
              </div>
            ))}
          </div>
        </section>

        <p className="mt-14 font-mono text-[11px] text-slate-600">
          Local only · /icon-review · bitmaps in client/src/lib/kareIcons.ts
        </p>
      </div>
    </div>
  );
}
