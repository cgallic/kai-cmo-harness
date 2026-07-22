import { NextResponse } from "next/server";

import { gateway, GatewayError } from "@/lib/gateway/client";
import type {
  AutopilotCommandCenterResponse,
  Bottleneck,
  PortfolioBrand,
} from "@/lib/gateway/types";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

interface GatewayBottleneck {
  brand_id: string;
  blocked_gate: string;
  owner: string;
  next_action: string;
  close_condition: string;
  evidence_refs?: string[];
  type?: string;
}

interface GatewayCommandCenter {
  generated_at: string;
  primary_bottleneck: GatewayBottleneck | null;
  coach: {
    status: string;
    message: string;
    next_action: string;
    close_condition: string;
    evidence_refs?: string[];
  };
}

interface GatewayPortfolioRow {
  brand_id: string;
  brand_name: string;
  lifecycle: string;
  health: string;
  blocked_gate: string | null;
  owner: string;
  next_action: string;
  close_condition: string;
  evidence_refs?: string[];
}

interface GatewayPortfolio {
  generated_at: string;
  rows: GatewayPortfolioRow[];
}

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const [commandCenter, portfolioResult] = await Promise.all([
      gateway<GatewayCommandCenter>("/ops/command-center", { timeout: 15000 }),
      gateway<GatewayPortfolio>("/ops/portfolio", { timeout: 15000 }),
    ]);

    const portfolio: PortfolioBrand[] = portfolioResult.rows.map((row) => ({
      brand_id: row.brand_id,
      brand_name: row.brand_name,
      lifecycle: row.lifecycle,
      health: row.health,
      blocked_gate: row.blocked_gate || "none",
      owner: row.owner,
      next_action: row.next_action,
      close_condition: row.close_condition,
      evidence_refs: row.evidence_refs || [],
    }));

    const rawBottleneck = commandCenter.primary_bottleneck;
    const bottleneckBrand = rawBottleneck
      ? portfolio.find((row) => row.brand_id === rawBottleneck.brand_id)
      : undefined;
    const primaryBottleneck: Bottleneck | null = rawBottleneck
      ? {
          brand_id: rawBottleneck.brand_id,
          brand_name: bottleneckBrand?.brand_name || rawBottleneck.brand_id,
          lifecycle: bottleneckBrand?.lifecycle || "unknown",
          health: bottleneckBrand?.health || "blocked",
          blocked_gate: rawBottleneck.blocked_gate,
          owner: rawBottleneck.owner,
          next_action: rawBottleneck.next_action,
          close_condition: rawBottleneck.close_condition,
          evidence_refs: rawBottleneck.evidence_refs || [],
          summary: rawBottleneck.type
            ? `The ${rawBottleneck.type.replace(/[_-]+/g, " ")} gate is the highest-priority constraint in the verified portfolio state.`
            : undefined,
          proof_state: "evidence_required",
        }
      : null;

    const response: AutopilotCommandCenterResponse = {
      primary_bottleneck: primaryBottleneck,
      coach: {
        state: commandCenter.coach.status,
        message: commandCenter.coach.message,
        next_action: commandCenter.coach.next_action,
        close_condition: commandCenter.coach.close_condition,
        evidence_refs: commandCenter.coach.evidence_refs || [],
      },
      portfolio,
      timestamp: commandCenter.generated_at || portfolioResult.generated_at,
    };

    return NextResponse.json(response, {
      headers: { "Cache-Control": "no-store" },
    });
  } catch (error: unknown) {
    const status = error instanceof GatewayError && error.status < 500 ? error.status : 502;
    const detail = error instanceof Error ? error.message : "Autopilot gateway unavailable";

    return NextResponse.json(
      {
        error: "Command Center unavailable",
        detail,
      },
      { status },
    );
  }
}
