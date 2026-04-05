import { createClient, createServiceClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

interface ExecuteRequest {
  action_id: string;
}

interface ProposedChanges {
  finding?: string;
  recommendation?: string;
  affected_url?: string;
}

interface ExecutionResult {
  type: string;
  deliverable: string;
  generated_at: string;
}

function generateDeliverable(
  actionType: string,
  proposedChanges: ProposedChanges
): ExecutionResult {
  const now = new Date().toISOString();

  switch (actionType) {
    case "update_copy":
    case "fix_cta":
      return {
        type: "copy_suggestion",
        deliverable: [
          `## Copy Improvement Suggestion`,
          ``,
          `**Finding:** ${proposedChanges.finding || "N/A"}`,
          ``,
          `**Recommendation:** ${proposedChanges.recommendation || "Review and update copy."}`,
          ``,
          `### Suggested Changes`,
          `- Review the current copy for clarity and conversion focus`,
          `- Ensure the primary CTA is visible above the fold`,
          `- Use action-oriented language (e.g., "Get Started", "Book Now", "Claim Your Spot")`,
          `- Include a phone number or click-to-call button if applicable`,
          `- Test headline variants with A/B testing`,
        ].join("\n"),
        generated_at: now,
      };

    case "add_schema":
      return {
        type: "schema_markup",
        deliverable: [
          `## JSON-LD Schema Markup`,
          ``,
          `**Finding:** ${proposedChanges.finding || "N/A"}`,
          ``,
          `### Recommended Schema`,
          "```json",
          JSON.stringify(
            {
              "@context": "https://schema.org",
              "@type": "LocalBusiness",
              name: "[Business Name]",
              url: proposedChanges.affected_url || "[URL]",
              telephone: "[Phone Number]",
              address: {
                "@type": "PostalAddress",
                streetAddress: "[Street]",
                addressLocality: "[City]",
                addressRegion: "[State]",
                postalCode: "[ZIP]",
              },
            },
            null,
            2
          ),
          "```",
          ``,
          `Add this to the \`<head>\` of your homepage.`,
        ].join("\n"),
        generated_at: now,
      };

    case "improve_speed":
      return {
        type: "optimization_recommendations",
        deliverable: [
          `## Performance Optimization Recommendations`,
          ``,
          `**Finding:** ${proposedChanges.finding || "N/A"}`,
          ``,
          `### Priority Fixes`,
          `1. **Image Optimization** - Compress images and serve in WebP/AVIF format`,
          `2. **Lazy Loading** - Defer off-screen images and iframes`,
          `3. **Minify CSS/JS** - Remove unused CSS and defer non-critical JavaScript`,
          `4. **Browser Caching** - Set Cache-Control headers for static assets`,
          `5. **CDN** - Serve assets from a CDN edge network`,
          `6. **Core Web Vitals** - Focus on LCP < 2.5s, CLS < 0.1, INP < 200ms`,
        ].join("\n"),
        generated_at: now,
      };

    case "fix_images":
      return {
        type: "image_fixes",
        deliverable: [
          `## Image Optimization Fixes`,
          ``,
          `**Finding:** ${proposedChanges.finding || "N/A"}`,
          ``,
          `### Action Items`,
          `- Add descriptive alt text to all images`,
          `- Compress images to reduce file size (target < 200KB per image)`,
          `- Use next-gen formats (WebP, AVIF) with fallbacks`,
          `- Set explicit width and height attributes to prevent CLS`,
          `- Use responsive images with srcset for different screen sizes`,
        ].join("\n"),
        generated_at: now,
      };

    case "fix_links":
      return {
        type: "link_fixes",
        deliverable: [
          `## Link Audit Results`,
          ``,
          `**Finding:** ${proposedChanges.finding || "N/A"}`,
          ``,
          `### Action Items`,
          `- Fix or remove all broken links (404s)`,
          `- Add internal links between related content pages`,
          `- Ensure important pages are within 3 clicks of the homepage`,
          `- Use descriptive anchor text (avoid "click here")`,
          `- Check for redirect chains and fix to single redirects`,
        ].join("\n"),
        generated_at: now,
      };

    case "improve_seo":
      return {
        type: "seo_improvements",
        deliverable: [
          `## SEO Improvement Plan`,
          ``,
          `**Finding:** ${proposedChanges.finding || "N/A"}`,
          ``,
          `### Priority Actions`,
          `- Optimize title tags (50-60 characters, primary keyword first)`,
          `- Write unique meta descriptions (120-155 characters)`,
          `- Use H1 tags correctly (one per page, includes target keyword)`,
          `- Improve internal linking structure`,
          `- Create content targeting high-intent keywords`,
          `- Submit updated sitemap to Google Search Console`,
        ].join("\n"),
        generated_at: now,
      };

    case "fix_mobile":
      return {
        type: "mobile_fixes",
        deliverable: [
          `## Mobile Optimization Fixes`,
          ``,
          `**Finding:** ${proposedChanges.finding || "N/A"}`,
          ``,
          `### Action Items`,
          `- Ensure viewport meta tag is set correctly`,
          `- Fix tap targets (minimum 48x48px)`,
          `- Eliminate horizontal scrolling`,
          `- Test forms and CTAs on mobile devices`,
          `- Optimize font sizes for readability (minimum 16px base)`,
        ].join("\n"),
        generated_at: now,
      };

    case "fix_social_meta":
      return {
        type: "social_meta_fixes",
        deliverable: [
          `## Social Meta Tag Fixes`,
          ``,
          `**Finding:** ${proposedChanges.finding || "N/A"}`,
          ``,
          `### Required Tags`,
          `- og:title - Page title for social sharing`,
          `- og:description - Description for social sharing`,
          `- og:image - Image URL (1200x630px recommended)`,
          `- og:url - Canonical URL`,
          `- twitter:card - Set to "summary_large_image"`,
        ].join("\n"),
        generated_at: now,
      };

    case "fix_security":
      return {
        type: "security_fixes",
        deliverable: [
          `## Security Fixes`,
          ``,
          `**Finding:** ${proposedChanges.finding || "N/A"}`,
          ``,
          `### Priority Actions`,
          `- Ensure SSL/TLS certificate is valid and not expired`,
          `- Redirect all HTTP traffic to HTTPS`,
          `- Set HSTS headers`,
          `- Review Content-Security-Policy headers`,
          `- Remove mixed content (HTTP resources on HTTPS pages)`,
        ].join("\n"),
        generated_at: now,
      };

    default:
      return {
        type: "general_recommendation",
        deliverable: [
          `## Improvement Recommendation`,
          ``,
          `**Finding:** ${proposedChanges.finding || "N/A"}`,
          ``,
          `**Recommendation:** ${proposedChanges.recommendation || "Review and address this finding."}`,
          ``,
          `### Next Steps`,
          `- Review the finding in detail`,
          `- Assess impact on user experience and conversions`,
          `- Prioritize fix based on severity and effort`,
          `- Implement changes and re-audit to verify`,
        ].join("\n"),
        generated_at: now,
      };
  }
}

export async function POST(request: Request) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const body: ExecuteRequest = await request.json();
  const { action_id } = body;

  if (!action_id) {
    return NextResponse.json(
      { error: "action_id is required" },
      { status: 400 }
    );
  }

  // Read action via user session (RLS ensures ownership)
  const { data: action } = await supabase
    .from("actions")
    .select("*")
    .eq("id", action_id)
    .single();

  if (!action) {
    return NextResponse.json({ error: "Action not found" }, { status: 404 });
  }

  if (action.approval_state !== "approved") {
    return NextResponse.json(
      { error: "Action must be approved before execution" },
      { status: 400 }
    );
  }

  const serviceClient = await createServiceClient();

  // Mark as executing
  await serviceClient
    .from("actions")
    .update({
      execution_state: "executing",
      updated_at: new Date().toISOString(),
    })
    .eq("id", action_id);

  try {
    // Generate deliverable based on action type
    const result = generateDeliverable(
      action.action_type,
      action.proposed_changes as ProposedChanges
    );

    // Mark as completed with result
    await serviceClient
      .from("actions")
      .update({
        execution_state: "completed",
        result_summary: result,
        executed_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })
      .eq("id", action_id);

    return NextResponse.json({
      status: "completed" as const,
      result,
    });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("Action execution failed:", message);

    // Mark as failed
    await serviceClient
      .from("actions")
      .update({
        execution_state: "failed",
        result_summary: { error: message },
        updated_at: new Date().toISOString(),
      })
      .eq("id", action_id);

    return NextResponse.json(
      { status: "failed" as const, error: message },
      { status: 500 }
    );
  }
}
