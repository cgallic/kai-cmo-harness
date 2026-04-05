import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4">
      <div className="text-center">
        <p className="font-mono text-6xl font-bold text-amber mb-4">404</p>
        <h1 className="font-display text-2xl font-semibold mb-2">
          Page not found
        </h1>
        <p className="text-text-secondary text-sm mb-8 max-w-sm">
          The page you are looking for does not exist or has been moved.
        </p>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 px-4 py-2 bg-amber text-background rounded-lg text-sm font-medium hover:bg-amber-light transition-colors"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10 19l-7-7m0 0l7-7m-7 7h18"
            />
          </svg>
          Back to dashboard
        </Link>
      </div>
    </div>
  );
}
