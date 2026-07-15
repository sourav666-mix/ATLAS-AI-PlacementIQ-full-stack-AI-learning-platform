// Reusable states so a page NEVER renders blank.
export function LoadingState({ label = "Loading…" }) {
  return (
    <div className="flex items-center justify-center py-16 text-slate-500">
      <span className="h-4 w-4 mr-3 rounded-full border-2 border-slate-300 border-t-slate-600 animate-spin" />
      {label}
    </div>
  );
}

export function EmptyState({ title = "Nothing here yet", hint, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="text-slate-800 font-medium">{title}</div>
      {hint && <div className="mt-1 text-sm text-slate-500 max-w-md">{hint}</div>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function ErrorState({ message = "Couldn't load this.", onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="text-red-600 font-medium">{message}</div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 px-4 py-2 rounded-lg bg-slate-900 text-white text-sm hover:bg-slate-700"
        >
          Try again
        </button>
      )}
    </div>
  );
}