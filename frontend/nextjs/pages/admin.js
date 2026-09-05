import { useEffect } from 'react';

const CANONICAL_ADMIN_URL = 'https://ready-2-robot.fly.dev/admin';

export default function LegacyAdminRedirect() {
  useEffect(() => {
    window.location.replace(CANONICAL_ADMIN_URL);
  }, []);

  return (
    <main className="min-h-screen bg-neutral-950 px-6 py-24 text-neutral-100">
      <section className="mx-auto max-w-xl border border-neutral-800 bg-neutral-900/60 p-6">
        <p className="text-xs uppercase tracking-[0.24em] text-emerald-400">Admin moved</p>
        <h1 className="mt-3 text-2xl font-bold">Ready For Robots Admin</h1>
        <p className="mt-3 text-sm leading-6 text-neutral-400">
          This legacy admin page has been retired so there is only one operational admin console.
        </p>
        <a
          href={CANONICAL_ADMIN_URL}
          className="mt-6 inline-flex border border-emerald-700 px-4 py-2 text-sm font-semibold text-emerald-300"
        >
          Open canonical admin
        </a>
      </section>
    </main>
  );
}
