import { createServiceClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";
import { PipedreamClient } from "@pipedream/sdk";

function getPd() {
  return new PipedreamClient({
    projectId: process.env.PIPEDREAM_PROJECT_ID!,
    projectEnvironment:
      (process.env.PIPEDREAM_ENVIRONMENT as "development" | "production") || "development",
    clientId: process.env.PIPEDREAM_CLIENT_ID!,
    clientSecret: process.env.PIPEDREAM_CLIENT_SECRET!,
  });
}

interface LinkedInOrganization {
  id: number;
  localizedName: string;
}

interface LinkedInOrgAclElement {
  "organizationalTarget~"?: LinkedInOrganization;
  organizationalTarget?: string;
}

interface LinkedInOrgAclsResponse {
  elements?: LinkedInOrgAclElement[];
}

export async function GET(request: NextRequest) {
  const brandId = request.nextUrl.searchParams.get("brand_id");
  if (!brandId) {
    return NextResponse.json({ error: "brand_id required" }, { status: 400 });
  }

  const serviceClient = await createServiceClient();

  const { data: integrations } = await serviceClient
    .from("integrations")
    .select("*")
    .eq("brand_id", brandId)
    .eq("provider", "linkedin")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0 || !integrations[0].connected_account_id) {
    return NextResponse.json({ organizations: [] });
  }

  const integration = integrations[0];

  try {
    const pd = getPd();
    const accountId = integration.connected_account_id;
    console.log("LinkedIn orgs: fetching with accountId:", accountId, "brandId:", brandId);

    const res = await pd.proxy.get({
      url: "https://api.linkedin.com/v2/organizationAcls?q=roleAssignee&role=ADMINISTRATOR&projection=(elements*(organizationalTarget~(id,localizedName)))",
      accountId,
      externalUserId: brandId,
    });

    // Pipedream SDK wraps response in { data: <body>, rawResponse: Response }
    const raw = res as Record<string, unknown>;
    console.log("LinkedIn orgs raw response keys:", Object.keys(raw));
    const body = (raw.data ?? raw) as LinkedInOrgAclsResponse;
    console.log("LinkedIn orgs body:", JSON.stringify(body).substring(0, 500));

    const organizations = (body?.elements || [])
      .map((el) => {
        const org = el["organizationalTarget~"];
        if (!org) return null;
        return { id: String(org.id), name: org.localizedName };
      })
      .filter(Boolean);

    console.log("LinkedIn orgs found:", organizations.length);
    return NextResponse.json({ organizations });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("LinkedIn organizations fetch error:", message);
    return NextResponse.json({ organizations: [], error: message });
  }
}
