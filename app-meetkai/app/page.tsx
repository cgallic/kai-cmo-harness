"use client";

import { useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const supabase = createClient();
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback`,
      },
    });

    setLoading(false);
    if (error) {
      setError(error.message);
    } else {
      setSent(true);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="font-display text-4xl font-bold tracking-tight mb-2">
            Meet<span className="text-amber">Kai</span>
          </h1>
          <p className="text-text-secondary text-sm">
            Your AI CMO Dashboard
          </p>
        </div>

        {/* Card */}
        <div className="bg-card border border-border rounded-[16px] p-8">
          {sent ? (
            <div className="text-center space-y-4">
              <div className="w-12 h-12 rounded-full bg-success-dim flex items-center justify-center mx-auto">
                <svg className="w-6 h-6 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div>
                <h2 className="font-display text-lg font-semibold mb-1">Check your email</h2>
                <p className="text-text-secondary text-sm">
                  We sent a magic link to <span className="text-foreground font-medium">{email}</span>
                </p>
              </div>
              <button
                onClick={() => { setSent(false); setEmail(""); }}
                className="text-text-tertiary text-sm hover:text-text-secondary transition-colors"
              >
                Use a different email
              </button>
            </div>
          ) : (
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-text-secondary mb-2">
                  Email address
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  required
                  className="w-full px-4 py-3 bg-background border border-border rounded-[12px] text-foreground placeholder:text-text-tertiary focus:outline-none focus:border-amber transition-colors"
                />
              </div>

              {error && (
                <p className="text-error text-sm">{error}</p>
              )}

              <Button type="submit" loading={loading} className="w-full" size="lg">
                Send magic link
              </Button>

              <p className="text-text-tertiary text-xs text-center">
                No password needed. We&apos;ll email you a secure login link.
              </p>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
