import Link from 'next/link';

interface BrowserAuthNoticeAction {
  label: string;
  href: string;
}

interface BrowserAuthNoticeProps {
  isAuthenticated: boolean;
  guestTitle: string;
  guestDescription: string;
  authenticatedTitle: string;
  authenticatedDescription: string;
  guestActions?: BrowserAuthNoticeAction[];
  authenticatedActions?: BrowserAuthNoticeAction[];
}

export default function BrowserAuthNotice({
  isAuthenticated,
  guestTitle,
  guestDescription,
  authenticatedTitle,
  authenticatedDescription,
  guestActions,
  authenticatedActions,
}: BrowserAuthNoticeProps) {
  const title = isAuthenticated ? authenticatedTitle : guestTitle;
  const description = isAuthenticated ? authenticatedDescription : guestDescription;
  const actions = isAuthenticated ? authenticatedActions : guestActions;

  return (
    <section className="rounded-3xl border border-amber-400/20 bg-amber-500/10 p-5 shadow-xl shadow-black/10 backdrop-blur">
      <p className="text-xs uppercase tracking-[0.24em] text-amber-50/80">Браузерная версия</p>
      <h2 className="mt-2 text-xl font-semibold text-white">{title}</h2>
      <p className="mt-3 max-w-3xl text-sm leading-6 text-amber-50/90">{description}</p>

      {actions && actions.length > 0 ? (
        <div className="mt-4 flex flex-wrap gap-3">
          {actions.map((action) => (
            <Link
              key={`${action.href}-${action.label}`}
              href={action.href}
              className="inline-flex rounded-2xl border border-white/10 bg-white/10 px-4 py-3 text-sm font-medium text-white transition hover:border-white/20 hover:bg-white/15"
            >
              {action.label}
            </Link>
          ))}
        </div>
      ) : null}
    </section>
  );
}
