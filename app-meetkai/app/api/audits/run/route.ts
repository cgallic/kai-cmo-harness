import { createClient, createServiceClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

/** MiKai audit dimension keys */
const AUDIT_DIMENSIONS = [
  "offer_clarity",
  "trust_and_proof",
  "conversion_path",
  "local_seo",
  "speed_to_lead",
  "reviews_reputation",
  "channel_presence",
  "follow_up_gaps",
] as const;

type AuditDimension = (typeof AUDIT_DIMENSIONS)[number];

/** Weights per dimension (sum = 1.0) */
const DIMENSION_WEIGHTS: Record<AuditDimension, number> = {
  offer_clarity: 0.15,
  trust_and_proof: 0.15,
  conversion_path: 0.15,
  local_seo: 0.1,
  speed_to_lead: 0.15,
  reviews_reputation: 0.1,
  channel_presence: 0.1,
  follow_up_gaps: 0.1,
};

interface MiKaiCategoryResult {
  score: number;
  findings?: Array<{
    severity?: string;
    title?: string;
    description?: string;
    recommendation?: string;
  }>;
}

interface MiKaiResponse {
  [key: string]: MiKaiCategoryResult | unknown;
}

function parseMiKaiResponse(raw: MiKaiResponse) {
  const categoryScores: Record<string, number> = {};
  const findings: Array<{
    category: string;
    severity: "critical" | "warning" | "info" | "pass";
    title: string;
    description: string;
    recommendation?: string;
  }> = [];

  for (const dim of AUDIT_DIMENSIONS) {
    const cat = raw[dim] as MiKaiCategoryResult | undefined;
    const score = typeof cat?.score === "number" ? cat.score : 0;
    categoryScores[dim] = Math.min(10, Math.max(0, score));

    if (cat?.findings && Array.isArray(cat.findings)) {
      for (const f of cat.findings) {
        const severity = (["critical", "warning", "info", "pass"] as const).includes(
          f.severity as "critical" | "warning" | "info" | "pass"
        )
          ? (f.severity as "critical" | "warning" | "info" | "pass")
          : "info";

        findings.push({
          category: dim,
          severity,
          title: f.title || dim.replace(/_/g, " "),
          description: f.description || "",
          recommendation: f.recommendation,
        });
      }
    }
  }

  // Weighted average -> 0-100
  let overallScore = 0;
  for (const dim of AUDIT_DIMENSIONS) {
    overallScore += (categoryScores[dim] / 10) * DIMENSION_WEIGHTS[dim] * 100;
  }

  return {
    overallScore: Math.round(overallScore),
    categoryScores,
    findings,
  };
}

export async function POST(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  let body: { brand_id: string; domain?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid request body" }, { status: 400 });
  }

  const { brand_id, domain } = body;

  if (!brand_id) {
    return NextResponse.json({ error: "brand_id is required" }, { status: 400 });
  }

  // Verify brand ownership
  const { data: brand, error: brandErr } = await supabase
    .from("brands")
    .select("id, name, url")
    .eq("id", brand_id)
    .eq("user_id", user.id)
    .single();

  if (brandErr || !brand) {
    return NextResponse.json({ error: "Brand not found", code: "BRAND_NOT_FOUND" }, { status: 404 });
  }

  const auditDomain = domain || brand.url;
  if (!auditDomain) {
    return NextResponse.json(
      { error: "No domain specified. Set a website URL in settings first." },
      { status: 400 }
    );
  }

  try {
    // Call MiKai audit API
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 60_000); // 60s timeout

    const miKaiRes = await fetch("https://meetkai.xyz/api/mikai/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        domain: auditDomain,
        email: user.email,
        name: brand.name,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeout);

    if (!miKaiRes.ok) {
      const errorText = await miKaiRes.text().catch(() => "Unknown error");
      console.error("MiKai API error:", miKaiRes.status, errorText);
      return NextResponse.json(
        { error: "Audit service returned an error", detail: errorText },
        { status: 502 }
      );
    }

    const miKaiData = (await miKaiRes.json()) as MiKaiResponse;
    const { overallScore, categoryScores, findings } = parseMiKaiResponse(miKaiData);

    // Insert into audits table via service role client
    const serviceClient = await createServiceClient();
    const { data: audit, error: insertError } = await serviceClient
      .from("audits")
      .insert({
        brand_id,
        overall_score: overallScore,
        category_scores: categoryScores,
        findings,
        metadata: { raw_response: miKaiData, domain: auditDomain },
        created_at: new Date().toISOString(),
      })
      .select("id, overall_score, category_scores, findings, created_at")
      .single();

    if (insertError) {
      console.error("Audit insert error:", insertError);
      return NextResponse.json(
        { error: "Failed to save audit results", detail: insertError.message },
        { status: 500 }
      );
    }

    return NextResponse.json({
      audit_id: audit.id,
      status: "completed" as const,
      overall_score: audit.overall_score,
      category_scores: audit.category_scores,
      findings: audit.findings,
      created_at: audit.created_at,
    });
  } catch (error: unknown) {
    if (error instanceof Error && error.name === "AbortError") {
      return NextResponse.json(
        { error: "Audit timed out. The site may be slow to respond." },
        { status: 504 }
      );
    }
    const message = error instanceof Error ? error.message : String(error);
    console.error("Audit run error:", message);
    return NextResponse.json({ error: "Audit failed", detail: message }, { status: 500 });
  }
}
