import { createClient, createServiceClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";
import type { AuditFinding } from "@/lib/types";

type ActionSource = "audit" | "analytics" | "manual";

interface GenerateRequest {
  brand_id: string;
  source: ActionSource;
}

interface ProposedChanges {
  finding: string;
  recommendation: string;
  affected_url: string;
}

interface ActionInsert {
  brand_id: string;
  action_type: string;
  channel: string;
  intent: string;
  risk_tier: "low" | "medium" | "high";
  proposed_changes: ProposedChanges;
  approval_state: "pending";
  execution_state: "pending";
}

function mapFindingToActionType(finding: AuditFinding): string {
  const title = finding.title.toLowerCase();
  const desc = finding.description.toLowerCase();
  const combined = `${title} ${desc}`;

  if (combined.includes("cta") || combined.includes("call to action")) return "fix_cta";
  if (combined.includes("schema") || combined.includes("structured data") || combined.includes("json-ld")) return "add_schema";
  if (combined.includes("speed") || combined.includes("performance") || combined.includes("load time") || combined.includes("core web vitals")) return "improve_speed";
  if (combined.includes("copy") || combined.includes("headline") || combined.includes("title tag") || combined.includes("meta description")) return "update_copy";
  if (combined.includes("mobile") || combined.includes("responsive")) return "fix_mobile";
  if (combined.includes("image") || combined.includes("alt text") || combined.includes("alt tag")) return "fix_images";
  if (combined.includes("link") || combined.includes("internal linking") || combined.includes("broken")) return "fix_links";
  if (combined.includes("seo") || combined.includes("keyword") || combined.includes("ranking")) return "improve_seo";
  if (combined.includes("social") || combined.includes("og tag") || combined.includes("open graph")) return "fix_social_meta";
  if (combined.includes("security") || combined.includes("ssl") || combined.includes("https")) return "fix_security";
  return "general_improvement";
}

function mapCategoryToChannel(category: string): string {
  const cat = category.toLowerCase();

  if (cat.includes("seo") || cat.includes("search")) return "seo";
  if (cat.includes("social")) return "social";
  if (cat.includes("email")) return "email";
  if (cat.includes("paid") || cat.includes("ads") || cat.includes("advertising")) return "paid_media";
  if (cat.includes("content")) return "content";
  if (cat.includes("analytics")) return "analytics";
  if (cat.includes("performance") || cat.includes("speed") || cat.includes("technical")) return "website";
  if (cat.includes("design") || cat.includes("ux") || cat.includes("ui")) return "website";
  return "website";
}

function generateHumanReadableIntent(finding: AuditFinding): string {
  if (finding.recommendation) {
    // Use the recommendation as the base, trim to a reasonable length
    const rec = finding.recommendation.trim();
    if (rec.length <= 120) return rec;
    return rec.slice(0, 117) + "...";
  }

  // Fall back to constructing from title
  return `Fix: ${finding.title}`;
}

export async function POST(request: Request) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const body: GenerateRequest = await request.json();
  const { brand_id, source } = body;

  if (!brand_id || !source) {
    return NextResponse.json(
      { error: "brand_id and source are required" },
      { status: 400 }
    );
  }

  // Verify brand ownership
  const { data: brand, error: brandErr } = await supabase
    .from("brands")
    .select("id, url")
    .eq("id", brand_id)
    .eq("user_id", user.id)
    .single();

  if (brandErr || !brand) {
    return NextResponse.json({ error: "Brand not found", code: "BRAND_NOT_FOUND" }, { status: 404 });
  }

  // Get latest audit — use .limit(1) instead of .single() to avoid throwing on 0 rows
  const { data: audits, error: auditErr } = await supabase
    .from("audits")
    .select("*")
    .eq("brand_id", brand_id)
    .order("created_at", { ascending: false })
    .limit(1);

  if (auditErr || !audits || audits.length === 0) {
    return NextResponse.json(
      { error: "No audit found. Run an audit first.", code: "NO_AUDIT" },
      { status: 404 }
    );
  }

  const audit = audits[0];

  // Parse findings — they're stored as jsonb
  const findings: AuditFinding[] = Array.isArray(audit.findings)
    ? audit.findings
    : [];

  // Filter to actionable findings (critical or warning)
  const actionableFindings = findings.filter(
    (f) => f.severity === "critical" || f.severity === "warning"
  );

  if (actionableFindings.length === 0) {
    return NextResponse.json({
      actions: [],
      count: 0,
      message: "No actionable findings found in the latest audit.",
    });
  }

  // Build action proposals
  const actionsToInsert: ActionInsert[] = actionableFindings.map((finding) => ({
    brand_id,
    action_type: mapFindingToActionType(finding),
    channel: mapCategoryToChannel(finding.category),
    intent: generateHumanReadableIntent(finding),
    risk_tier: finding.severity === "critical" ? "medium" : "low",
    proposed_changes: {
      finding: finding.description,
      recommendation: finding.recommendation || "",
      affected_url: brand.url || "",
    },
    approval_state: "pending" as const,
    execution_state: "pending" as const,
  }));

  // Insert via service role to bypass RLS
  const serviceClient = await createServiceClient();
  const { data: createdActions, error: insertError } = await serviceClient
    .from("actions")
    .insert(actionsToInsert)
    .select();

  if (insertError) {
    console.error("Failed to insert actions:", insertError);
    return NextResponse.json(
      { error: "Failed to create actions" },
      { status: 500 }
    );
  }

  return NextResponse.json({
    actions: createdActions,
    count: createdActions.length,
  });
}
