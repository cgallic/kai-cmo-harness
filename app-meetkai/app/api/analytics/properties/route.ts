import { createClient, createServiceClient } from "@/lib/supabase/server";
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

interface PropertySummary {
  property: string;
  displayName: string;
}

interface AccountSummary {
  displayName: string;
  propertySummaries?: PropertySummary[];
}

interface AccountSummariesResponse {
  accountSummaries?: AccountSummary[];
}

export interface GA4Property {
  property_id: string;
  display_name: string;
  account_name: string;
}

export async function GET(request: NextRequest) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const brandId = request.nextUrl.searchParams.get("brand_id");
  if (!brandId) {
    return NextResponse.json({ error: "brand_id is required" }, { status: 400 });
  }

  // Verify brand ownership
  const { data: brand } = await supabase
    .from("brands")
    .select("id")
    .eq("id", brandId)
    .eq("user_id", user.id)
    .single();

  if (!brand) {
    return NextResponse.json({ error: "Brand not found" }, { status: 404 });
  }

  const serviceClient = await createServiceClient();

  const { data: integration } = await serviceClient
    .from("integrations")
    .select("*")
    .eq("brand_id", brandId)
    .eq("provider", "ga4")
    .eq("status", "connected")
    .single();

  if (!integration?.connected_account_id) {
    return NextResponse.json(
      { error: "Google Analytics not connected" },
      { status: 404 }
    );
  }

  try {
    const pd = getPd();
    const adminRes = await pd.proxy.get({
      url: "https://analyticsadmin.googleapis.com/v1beta/accountSummaries",
      accountId: integration.connected_account_id,
      externalUserId: brandId,
    });

    const adminData = ((adminRes as { data?: AccountSummariesResponse })?.data ??
      adminRes) as AccountSummariesResponse;

    const properties: GA4Property[] = [];
    const summaries = adminData?.accountSummaries;
    if (summaries) {
      for (const acct of summaries) {
        if (acct.propertySummaries?.length) {
          for (const prop of acct.propertySummaries) {
            properties.push({
              property_id: prop.property,
              display_name: prop.displayName,
              account_name: acct.displayName,
            });
          }
        }
      }
    }

    return NextResponse.json({ properties });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("GA4 properties error:", message);
    return NextResponse.json(
      { error: "Failed to fetch properties", detail: message },
      { status: 502 }
    );
  }
}
