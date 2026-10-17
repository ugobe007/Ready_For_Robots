import { FormEvent } from "react";

type UrlInputProps = {
  value: string;
  onChange: (value: string) => void;
  onSubmit?: (value: string) => void;
  label?: string;
  placeholder?: string;
  id?: string;
  submitLabel?: string;
};

export function UrlInput({
  value,
  onChange,
  onSubmit,
  label = "Robot product page",
  placeholder = "https://",
  id = "robot-product-page",
  submitLabel = "Find buyers →",
}: UrlInputProps) {
  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    onSubmit?.(value);
  }

  return (
    <form onSubmit={handleSubmit}>
      <label htmlFor={id}>
        <span className="rfr-url-label">{label}</span>
        <span className="rfr-url-row">
          <input
            id={id}
            type="text"
            inputMode="url"
            name="robot-url"
            value={value}
            placeholder={placeholder}
            onChange={(event) => onChange(event.target.value)}
          />
          <button type="submit">{submitLabel}</button>
        </span>
      </label>
    </form>
  );
}
