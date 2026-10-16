type ExampleBadgeProps = {
  children?: string;
};

export function ExampleBadge({ children = "EXAMPLE" }: ExampleBadgeProps) {
  return <span className="rfr-example">{children}</span>;
}
