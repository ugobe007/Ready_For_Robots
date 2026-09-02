/**
 * 1-bit Kare icons for `/` landing. Source: docs/rfr-70s-ui-source Home.tsx.
 * FIND / CRM keep the product face in kareIcons.ts.
 */

type PixelGridProps = {
  rows: readonly string[];
  size: number;
  color: string;
};

function PixelGrid({ rows, size, color }: PixelGridProps) {
  const width = rows[0]?.length ?? 0;
  const height = rows.length;
  const cell = 100 / Math.max(width, height, 1);
  const pixels: { x: number; y: number }[] = [];
  for (let y = 0; y < height; y += 1) {
    const row = rows[y] ?? "";
    for (let x = 0; x < row.length; x += 1) {
      if (row[x] === "X") pixels.push({ x, y });
    }
  }
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      shapeRendering="crispEdges"
      aria-hidden="true"
    >
      {pixels.map(pixel => (
        <rect
          key={`${pixel.x}-${pixel.y}`}
          x={pixel.x * cell}
          y={pixel.y * cell}
          width={cell}
          height={cell}
          fill={color}
        />
      ))}
    </svg>
  );
}

const ROBOT_ROWS = [
  ".....XX.....",
  ".....XX.....",
  "..XXXXXXXX..",
  ".X........X.",
  ".X.XX..XX.X.",
  ".X........X.",
  ".X........X.",
  ".X.XXXXXX.X.",
  ".X........X.",
  "..XXXXXXXX..",
  "............",
  "............",
] as const;

const BRIEFCASE_ROWS = [
  "....XXXX....",
  "...X....X...",
  "...X....X...",
  ".XXXXXXXXXX.",
  ".X....X...X.",
  ".XXXXXXXXXX.",
  ".X........X.",
  ".X........X.",
  ".XXXXXXXXXX.",
] as const;

const DOC_ROWS = [
  ".XXXXXXXX...",
  ".X......X...",
  ".X.XXXX.X...",
  ".X......X...",
  ".X.XXXX.X...",
  ".X......X...",
  ".X.XXXX.X...",
  ".X......X...",
  ".XXXXXXXX...",
] as const;

const HAND_ROWS = [
  "..XX........",
  ".X..X.......",
  ".X..X.XXX...",
  ".X..XX...XX.",
  ".X..X......X",
  "..X........X",
  "...X......X.",
  "....X....X..",
  ".....XXXX...",
] as const;

export function PixelRobot({
  size = 32,
  color,
}: {
  size?: number;
  color: string;
}) {
  return <PixelGrid rows={ROBOT_ROWS} size={size} color={color} />;
}

export function PixelBriefcase({
  size = 28,
  color,
}: {
  size?: number;
  color: string;
}) {
  return <PixelGrid rows={BRIEFCASE_ROWS} size={size} color={color} />;
}

export function PixelDoc({
  size = 22,
  color,
}: {
  size?: number;
  color: string;
}) {
  return <PixelGrid rows={DOC_ROWS} size={size} color={color} />;
}

export function PixelHand({
  size = 20,
  color,
}: {
  size?: number;
  color: string;
}) {
  return <PixelGrid rows={HAND_ROWS} size={size} color={color} />;
}
