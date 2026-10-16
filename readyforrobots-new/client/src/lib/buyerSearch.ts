/**
 * Which screen a robot-job-search payload is.
 * Classified jobs → results. A homepage lineup → picker.
 * An unrecognized product page → the honest empty state.
 */

export type BuyerSearchView = "results" | "picker" | "class" | "unrecognized";

export type BuyerSearchPayload = {
  state?: string | null;
  needs_product_choice?: boolean | null;
  needs_class_choice?: boolean | null;
  zero_reason?: string | null;
};

export function buyerSearchView(payload: BuyerSearchPayload): BuyerSearchView {
  if (payload.needs_product_choice || payload.state === "select_product") {
    return "picker";
  }
  if (payload.needs_class_choice || payload.state === "qualify_robot") {
    return "class";
  }
  if (
    payload.zero_reason === "unrecognized_product" ||
    payload.state === "could_not_understand"
  ) {
    return "unrecognized";
  }
  return "results";
}
