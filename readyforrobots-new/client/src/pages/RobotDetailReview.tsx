import { Link, useParams } from "wouter";
import { ArrowLeft } from "lucide-react";

/** Confirmed robot profile shell — Slice 1 landing after confirm. */
export default function RobotDetailReview() {
  const params = useParams<{ robotId: string }>();
  const profile =
    typeof window !== "undefined"
      ? new URLSearchParams(window.location.search).get("profile")
      : null;

  return (
    <main className="min-h-screen bg-[#081126] text-[#edf4f3]">
      <div className="mx-auto max-w-3xl px-5 py-10">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm text-slate-300 hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" /> Home
        </Link>
        <p className="mt-8 text-[10px] font-semibold uppercase tracking-[0.36em] text-[#7adfc8]">
          Confirmed Profile
        </p>
        <h1 className="mt-3 text-3xl font-semibold text-slate-50">
          Robot #{params.robotId}
        </h1>
        <p className="mt-3 text-sm text-slate-300">
          Immutable profile version {profile || "saved"}. Facility opportunity
          search lands in Slice 2–5.
        </p>
        <Link
          href={`/robots/${params.robotId}/opportunities`}
          className="mt-8 inline-flex text-sm font-semibold text-[#00d0a2] hover:text-[#4cf0c8]"
        >
          Find its jobs →
        </Link>
      </div>
    </main>
  );
}
