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
    const res = await pd.proxy.get({
      url: "https://api.linkedin.com/v2/organizationAcls?q=roleAssignee&role=ADMINISTRATOR&projection=(elements*(organizationalTarget~(id,localizedName)))",
      accountId: integration.connected_account_id,
      externalUserId: brandId,
    });

    const data = ((res as { data?: LinkedInOrgAclsResponse })?.data ?? res) as LinkedInOrgAclsResponse;
    const organizations = (data?.elements || [])
      .map((el) => {
        const org = el["organizationalTarget~"];
        if (!org) return null;
        return { id: String(org.id), name: org.localizedName };
      })
      .filter(Boolean);

    return NextResponse.json({ organizations });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("LinkedIn organizations fetch error:", message);
    return NextResponse.json({ organizations: [], error: message });
  }
}
