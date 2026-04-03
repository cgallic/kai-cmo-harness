import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const next = searchParams.get("next") ?? "/dashboard";

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);

    if (!error) {
      // Check if user has a brand
      const { data: { user } } = await supabase.auth.getUser();
      if (user) {
        const { data: brands } = await supabase
          .from("brands")
          .select("id")
          .eq("user_id", user.id)
          .limit(1);

        // No brand yet → send to settings for onboarding
        if (!brands || brands.length === 0) {
          return NextResponse.redirect(`${origin}/settings?onboarding=true`);
        }
      }

      return NextResponse.redirect(`${origin}${next}`);
    }
  }

  // Auth error → back to login
  return NextResponse.redirect(`${origin}/?error=auth_failed`);
}
