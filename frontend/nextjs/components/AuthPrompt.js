/**
 * AuthPrompt — shown when an unauthenticated user clicks "Follow Up" or "Save".
 * Drop-in modal that prompts the user to create an account or sign in.
 */
export default function AuthPrompt({ onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-sm bg-[#0c0c0c] border border-neutral-700 rounded-lg shadow-2xl p-6 z-10">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-neutral-600 hover:text-neutral-300 text-sm leading-none"
        >
          ✕
        </button>

        <div className="mb-5">
          <p className="text-sm font-semibold text-white mb-1.5">Save leads &amp; track follow-ups</p>
          <p className="text-xs text-neutral-500 leading-relaxed">
            Create a free account to bookmark companies, queue follow-ups, and build outreach target lists.
          </p>
        </div>

        <div className="flex gap-2">
          <a
            href="/login?mode=signup"
            className="flex-1 text-center py-2 px-4 border border-emerald-700 text-emerald-400 hover:border-emerald-500 hover:text-emerald-300 rounded text-xs font-medium transition-colors"
          >
            Create account
          </a>
          <a
            href="/login"
            className="flex-1 text-center py-2 px-4 border border-neutral-700 text-neutral-400 hover:border-neutral-500 hover:text-neutral-200 rounded text-xs transition-colors"
          >
            Sign in
          </a>
        </div>
      </div>
    </div>
  );
}
