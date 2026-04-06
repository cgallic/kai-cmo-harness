import { createClient, createServiceClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";
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

interface HubSpotCrmResponse {
  total?: number;
  results?: HubSpotDeal[];
}

interface HubSpotDeal {
  id: string;
  properties: {
    amount?: string | null;
    dealstage?: string | null;
    pipeline?: string | null;
  };
}

interface HubSpotPipelineStage {
  id: string;
  label: string;
}

interface HubSpotPipeline {
  id: string;
  label: string;
  stages: HubSpotPipelineStage[];
}

interface HubSpotPipelinesResponse {
  results?: HubSpotPipeline[];
}

export async function POST(request: Request) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { brand_id } = await request.json();

  const { data: brand } = await supabase
    .from("brands")
    .select("id")
    .eq("id", brand_id)
    .eq("user_id", user.id)
    .single();

  if (!brand) {
    return NextResponse.json({ error: "Brand not found" }, { status: 404 });
  }

  const serviceClient = await createServiceClient();

  const { data: integrations } = await serviceClient
    .from("integrations")
    .select("*")
    .eq("brand_id", brand_id)
    .eq("provider", "hubspot")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0) {
    return NextResponse.json({ error: "HubSpot not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const integration = integrations[0];
  if (!integration.connected_account_id) {
    return NextResponse.json({ error: "HubSpot not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const accountId = integration.connected_account_id;

  try {
    const pd = getPd();

    // Fetch contacts count
    const contactsRes = await pd.proxy.get({
      url: "https://api.hubapi.com/crm/v3/objects/contacts?limit=1",
      accountId,
      externalUserId: brand_id,
    });
    const contactsData = ((contactsRes as { data?: HubSpotCrmResponse })?.data ?? contactsRes) as HubSpotCrmResponse;
    const contactsCount = contactsData.total ?? 0;

    // Fetch deals (up to 100 with properties)
    const dealsRes = await pd.proxy.get({
      url: "https://api.hubapi.com/crm/v3/objects/deals?limit=100&properties=amount,dealstage,pipeline",
      accountId,
      externalUserId: brand_id,
    });
    const dealsData = ((dealsRes as { data?: HubSpotCrmResponse })?.data ?? dealsRes) as HubSpotCrmResponse;
    const deals = dealsData.results ?? [];
    const dealsCount = deals.length;
    const dealsTotalValue = deals.reduce((sum, deal) => {
      const amount = parseFloat(deal.properties?.amount ?? "0") || 0;
      return sum + amount;
    }, 0);

    // Fetch companies count
    const companiesRes = await pd.proxy.get({
      url: "https://api.hubapi.com/crm/v3/objects/companies?limit=1",
      accountId,
      externalUserId: brand_id,
    });
    const companiesData = ((companiesRes as { data?: HubSpotCrmResponse })?.data ?? companiesRes) as HubSpotCrmResponse;
    const companiesCount = companiesData.total ?? 0;

    // Fetch deal pipelines
    const pipelinesRes = await pd.proxy.get({
      url: "https://api.hubapi.com/crm/v3/pipelines/deals",
      accountId,
      externalUserId: brand_id,
    });
    const pipelinesData = ((pipelinesRes as { data?: HubSpotPipelinesResponse })?.data ?? pipelinesRes) as HubSpotPipelinesResponse;
    const pipelines = (pipelinesData.results ?? []).map((p) => ({
      name: p.label,
      stages_count: p.stages?.length ?? 0,
    }));

    const snapshot = {
      contacts_count: contactsCount,
      deals_count: dealsCount,
      deals_total_value: Math.round(dealsTotalValue * 100) / 100,
      companies_count: companiesCount,
      pipelines,
    };

    await serviceClient.from("channel_snapshots").insert({
      brand_id,
      channel: "crm",
      provider: "hubspot",
      snapshot_data: snapshot,
    });

    await serviceClient
      .from("integrations")
      .update({ last_sync_at: new Date().toISOString() })
      .eq("id", integration.id);

    return NextResponse.json({ status: "synced", data: snapshot });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("HubSpot sync error:", message);
    return NextResponse.json({ error: "Sync failed", code: "SYNC_FAILED", detail: message }, { status: 500 });
  }
}
