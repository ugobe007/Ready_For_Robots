type EyebrowProps = {
  label: string;
  aside?: string;
};

export function Eyebrow({ label, aside }: EyebrowProps) {
  return (
    <div className="rfr-eyebrow">
      <span>{label}</span>
      {aside ? <span>{aside}</span> : null}
    </div>
  );
}
