import { FormEvent } from "react";

type UrlInputProps = {
  value: string;
  onChange: (value: string) => void;
  onSubmit?: (value: string) => void;
  label?: string;
};

export function UrlInput({
  value,
  onChange,
  onSubmit,
  label = "Robot product page",
}: UrlInputProps) {
  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    onSubmit?.(value);
  }

  return (
    <form onSubmit={handleSubmit}>
      <label>
        <span className="rfr-url-label">{label}</span>
        <span className="rfr-url-row">
          <input
            type="url"
            name="robot-url"
            value={value}
            placeholder="https://"
            onChange={(event) => onChange(event.target.value)}
          />
          <button type="submit">Find buyers →</button>
        </span>
      </label>
    </form>
  );
}
