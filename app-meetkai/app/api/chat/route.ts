import { streamText, tool } from "ai";
import { anthropic } from "@ai-sdk/anthropic";
import { z } from "zod";
import { createClient } from "@/lib/supabase/server";
import { gateway } from "@/lib/gateway/client";

export const maxDuration = 60;

export async function POST(req: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return new Response("Unauthorized", { status: 401 });
  }

  // Get brand context
  const { data: brands } = await supabase
    .from("brands")
    .select("id, name, url, archetype, metadata")
    .eq("user_id", user.id)
    .order("created_at", { ascending: false })
    .limit(1);
  const brand = brands?.[0];

  // Get latest audit score
  let auditScore: number | null = null;
  if (brand) {
    const { data: audits } = await supabase
      .from("audits")
      .select("overall_score")
      .eq("brand_id", brand.id)
      .order("created_at", { ascending: false })
      .limit(1);
    auditScore = audits?.[0]?.overall_score ?? null;
  }

  // Get connected channels
  let connectedChannels: string[] = [];
  if (brand) {
    const { data: integrations } = await supabase
      .from("integrations")
      .select("provider, channel")
      .eq("brand_id", brand.id)
      .eq("status", "connected");
    connectedChannels = (integrations || []).map(
      (i: { provider: string; channel: string }) =>
        `${i.provider} (${i.channel})`,
    );
  }

  const { messages } = await req.json();

  const systemPrompt = [
    `You are Kai, an AI CMO assistant for ${brand?.name || "a business"}.`,
    brand?.url ? `Website: ${brand.url}` : "",
    brand?.archetype ? `Business type: ${brand.archetype}` : "",
    auditScore != null
      ? `Current marketing health score: ${auditScore}/100`
      : "No audit run yet.",
    connectedChannels.length > 0
      ? `Connected channels: ${connectedChannels.join(", ")}`
      : "No channels connected yet.",
    "",
    "You help the business owner understand their marketing performance and take action.",
    "Use tools to fetch data and execute marketing tasks. Be concise and actionable.",
    "When the user asks to create content, use the generate_content tool.",
    "When they ask about their score or marketing health, use get_score.",
  ]
    .filter(Boolean)
    .join("\n");

  const result = streamText({
    model: anthropic("claude-sonnet-4-20250514"),
    system: systemPrompt,
    messages,
    tools: {
      run_audit: tool({
        description: "Run a marketing audit on the user's website",
        inputSchema: z.object({
          domain: z
            .string()
            .optional()
            .describe("Domain to audit (uses brand URL if omitted)"),
        }),
        execute: async (_input: { domain?: string }) => {
          if (!brand)
            return { error: "No brand profile found. Set up your profile first." };
          try {
            const res = await gateway(`/kai-operator/audit/${brand.id}`, {
              params: { scope: "full" },
              timeout: 120000,
            });
            return { success: true, data: res };
          } catch (e) {
            return { error: e instanceof Error ? e.message : "Audit failed" };
          }
        },
      }),
      generate_content: tool({
        description:
          "Generate marketing content (blog, email, social, ads, landing page)",
        inputSchema: z.object({
          format: z.enum([
            "blog",
            "email",
            "cold-email",
            "linkedin",
            "meta-ads",
            "google-ads",
            "tiktok",
            "landing-page",
            "press",
          ]),
          keyword: z.string().describe("Topic or keyword for the content"),
          persona: z.string().optional().describe("Target persona"),
        }),
        execute: async (input: {
          format: string;
          keyword: string;
          persona?: string;
        }) => {
          if (!brand) return { error: "No brand profile found." };
          try {
            const res = await gateway("/generate", {
              method: "POST",
              body: {
                format: input.format,
                keyword: input.keyword,
                persona: input.persona,
                site: brand.name.toLowerCase().replace(/\s+/g, "-"),
                brand_id: brand.id,
                surface: "remote",
              },
              timeout: 60000,
            });
            return { success: true, data: res };
          } catch (e) {
            return {
              error: e instanceof Error ? e.message : "Generation failed",
            };
          }
        },
      }),
      get_analytics: tool({
        description:
          "Get current analytics data (traffic, rankings, performance)",
        inputSchema: z.object({
          channel: z.enum(["ga4", "gsc", "all"]).default("all"),
        }),
        execute: async (_input: { channel: string }) => {
          if (!brand) return { error: "No brand profile found." };
          try {
            const res = await gateway("/webhooks/analytics/summary", {
              method: "POST",
              body: {
                client: brand.name.toLowerCase().replace(/\s+/g, "-"),
              },
            });
            return { success: true, data: res };
          } catch (e) {
            return {
              error:
                e instanceof Error ? e.message : "Analytics fetch failed",
            };
          }
        },
      }),
      propose_actions: tool({
        description: "Generate action proposals from latest audit findings",
        inputSchema: z.object({}),
        execute: async (_input: Record<string, never>) => {
          if (!brand) return { error: "No brand profile found." };
          try {
            const res = await gateway("/ops/dashboard", {
              params: { brand_id: brand.id },
            });
            return { success: true, data: res };
          } catch (e) {
            return {
              error:
                e instanceof Error ? e.message : "Failed to get proposals",
            };
          }
        },
      }),
      approve_action: tool({
        description: "Approve a pending action by ID",
        inputSchema: z.object({
          action_id: z.string().describe("The action ID to approve"),
        }),
        execute: async (input: { action_id: string }) => {
          try {
            const res = await gateway(
              `/ops/proposals/${input.action_id}/approve`,
              {
                method: "POST",
              },
            );
            return { success: true, data: res };
          } catch (e) {
            return {
              error: e instanceof Error ? e.message : "Approval failed",
            };
          }
        },
      }),
      get_score: tool({
        description: "Get current marketing health score and breakdown",
        inputSchema: z.object({}),
        execute: async (_input: Record<string, never>) => {
          if (!brand) return { error: "No brand profile found." };
          const { data: audits } = await supabase
            .from("audits")
            .select("overall_score, category_scores, findings, created_at")
            .eq("brand_id", brand.id)
            .order("created_at", { ascending: false })
            .limit(1);
          const latest = audits?.[0];
          if (!latest)
            return { score: null, message: "No audit has been run yet." };
          return {
            score: latest.overall_score,
            categories: latest.category_scores,
            finding_count: Array.isArray(latest.findings)
              ? latest.findings.length
              : 0,
            audited_at: latest.created_at,
          };
        },
      }),
      run_skill: tool({
        description: "Run a specific Kai marketing skill",
        inputSchema: z.object({
          skill: z.enum([
            "kai-seo-audit",
            "kai-cro",
            "kai-landing-page",
            "kai-email-system",
            "kai-ad-campaign",
            "kai-social",
            "kai-cold-outreach",
            "kai-competitors",
            "kai-content-calendar",
            "kai-brand",
            "kai-growth-plan",
          ]),
          context: z
            .string()
            .optional()
            .describe("Additional context for the skill"),
        }),
        execute: async (input: { skill: string; context?: string }) => {
          if (!brand) return { error: "No brand profile found." };
          const generationFormatBySkill: Record<string, string> = {
            "kai-landing-page": "landing-page",
            "kai-email-system": "email-lifecycle",
            "kai-ad-campaign": "meta-ads",
            "kai-social": "tiktok",
            "kai-cold-outreach": "cold-email",
            "kai-content-calendar": "blog",
          };
          const format = generationFormatBySkill[input.skill];
          if (!format) {
            return {
              error: `${input.skill} is not a content-generation workflow yet. Use run_audit or propose_actions for audit/planning skills.`,
            };
          }
          try {
            const res = await gateway("/generate", {
              method: "POST",
              body: {
                format,
                workflow: input.skill,
                keyword: input.context || brand.name,
                site: brand.name.toLowerCase().replace(/\s+/g, "-"),
                brand_id: brand.id,
                surface: "remote",
              },
              timeout: 60000,
            });
            return { success: true, data: res };
          } catch (e) {
            return {
              error:
                e instanceof Error ? e.message : "Skill execution failed",
            };
          }
        },
      }),
    },
  });

  return result.toUIMessageStreamResponse();
}
