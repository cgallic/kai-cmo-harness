"use client";

import { useState } from "react";
import { ArrowRight, CheckCircle2 } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";

export function MagicLinkCard() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    if (
      !process.env.NEXT_PUBLIC_SUPABASE_URL ||
      !process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
    ) {
      setLoading(false);
      setError("Supabase is not configured for this local build.");
      return;
    }

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
    <div className="operator-login-card">
      <div className="mb-7">
        <div className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-lg border border-[#12121a]/20 bg-[#12121a] font-display text-2xl font-black text-cream shadow-[3px_3px_0_#d89d34]">
          K
        </div>
        <h2 className="font-display text-3xl font-bold tracking-normal">
          Sign in to MeetKai
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-[#5d625e]">
          The hosted dashboard for marketing audits, approvals, content, integrations,
          and run history.
        </p>
      </div>

      {sent ? (
        <div className="space-y-5 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-lg border border-success/20 bg-success-dim">
            <CheckCircle2 className="h-7 w-7 text-success" />
          </div>
          <div>
            <h3 className="font-display text-xl font-semibold">Check your email</h3>
            <p className="mt-2 text-sm text-[#5d625e]">
              We sent a secure operator link to{" "}
              <span className="font-semibold text-[#12121a]">{email}</span>.
            </p>
          </div>
          <button
            onClick={() => {
              setSent(false);
              setEmail("");
            }}
            className="text-sm font-semibold text-[#17416e] hover:underline"
          >
            Use a different email
          </button>
        </div>
      ) : (
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label htmlFor="email" className="mb-2 block text-sm font-semibold text-[#30322f]">
              Work email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              required
              className="operator-field"
            />
          </div>

          {error && <p className="text-sm font-medium text-error">{error}</p>}

          <Button type="submit" loading={loading} className="w-full" size="lg">
            Send operator link
            {!loading && <ArrowRight className="h-4 w-4" />}
          </Button>

          <p className="text-center text-xs leading-relaxed text-[#76766f]">
            No password. The link opens your approval queue, account map, and run ledger.
          </p>
        </form>
      )}
    </div>
  );
}
