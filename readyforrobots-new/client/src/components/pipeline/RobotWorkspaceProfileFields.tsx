import { ROBOT_CATEGORY_OPTIONS, type RobotWorkspaceProfile } from "@/lib/robotWorkspaceProfile";

type Props = {
  value: RobotWorkspaceProfile;
  onChange: (next: RobotWorkspaceProfile) => void;
  submittedHostname?: string;
  tone?: "dark" | "light";
  idPrefix?: string;
};

export default function RobotWorkspaceProfileFields({
  value,
  onChange,
  submittedHostname,
  tone = "dark",
  idPrefix = "rfr-profile",
}: Props) {
  const label = tone === "dark" ? "text-emerald-200/90" : "text-slate-700";
  const input =
    tone === "dark"
      ? "w-full rounded-xl border border-emerald-500/35 bg-black/30 px-3 py-2.5 text-sm text-emerald-50 placeholder:text-emerald-200/40 outline-none focus:border-emerald-300"
      : "w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 outline-none focus:border-amber-500";

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <label className="block sm:col-span-2">
        <span className={`mb-1.5 block text-[11px] font-bold uppercase tracking-[0.16em] ${label}`}>
          Customer / company name
        </span>
        <input
          id={`${idPrefix}-company`}
          value={value.company_name}
          onChange={(e) => onChange({ ...value, company_name: e.target.value })}
          placeholder={submittedHostname ? `e.g. company behind ${submittedHostname}` : "e.g. Reflex Robotics"}
          className={input}
          autoComplete="organization"
        />
      </label>
      <label className="block">
        <span className={`mb-1.5 block text-[11px] font-bold uppercase tracking-[0.16em] ${label}`}>
          Robot category
        </span>
        <select
          id={`${idPrefix}-category`}
          value={value.category}
          onChange={(e) => onChange({ ...value, category: e.target.value })}
          className={input}
        >
          <option value="">Select category…</option>
          {ROBOT_CATEGORY_OPTIONS.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      </label>
      <label className="block">
        <span className={`mb-1.5 block text-[11px] font-bold uppercase tracking-[0.16em] ${label}`}>
          Ideal customer (ICP)
        </span>
        <input
          id={`${idPrefix}-icp`}
          value={value.icp}
          onChange={(e) => onChange({ ...value, icp: e.target.value })}
          placeholder="e.g. 3PLs, food DCs, hospital systems"
          className={input}
        />
      </label>
    </div>
  );
}
