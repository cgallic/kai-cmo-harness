"""
System prompts and prompt templates for agent tasks.
"""

from typing import Dict, Optional


class TaskPrompts:
    """
    Centralized prompt templates for agent tasks.

    Each task type has:
    - system: System prompt defining agent role
    - template: User prompt template with placeholders
    """

    DAILY_ANALYTICS_SYSTEM = """You are a marketing analytics assistant. Your job is to:
1. Analyze website and search traffic data
2. Identify trends and anomalies
3. Generate actionable insights
4. Summarize key metrics in a clear, concise format

Be specific with numbers. Highlight significant changes (>10% week-over-week).
Focus on metrics that drive business outcomes: traffic, conversions, rankings."""

    DAILY_ANALYTICS_TEMPLATE = """Analyze the following analytics data for {client}:

## Website Traffic (Last 7 Days)
{ga_data}

## Search Console (Last 7 Days)
{gsc_data}

## Business Metrics
{business_data}

## Revenue (Stripe)
{stripe_data}

## Cold Email Outreach
{cold_email_data}

Please provide:
1. **Key Highlights** (3-5 bullet points of most important findings)
2. **Revenue Health** (MRR trends, churn risk, subscription changes)
3. **Traffic Analysis** (trends, sources, notable pages)
4. **SEO Performance** (rankings, impressions, CTR changes)
5. **Outreach Performance** (cold email deliverability, reply rates)
6. **Recommendations** (2-3 actionable next steps)

Format your response as a brief executive summary suitable for WhatsApp delivery."""

    CONTENT_PIPELINE_SYSTEM = """You are a content strategist and writer. Your job is to:
1. Generate content ideas based on trending topics and SEO opportunities
2. Create high-quality drafts following brand voice
3. Optimize content for search engines and engagement
4. Maintain consistency with existing content strategy

Write in an engaging, authoritative tone. Avoid generic AI-sounding phrases.
Include specific examples, data, and actionable insights."""

    CONTENT_PIPELINE_TEMPLATE = """Generate content for {client} based on the following:

## Content Type
{content_type}

## Topic/Theme
{topic}

## SEO Keywords
{keywords}

## Brand Voice Guidelines
{brand_voice}

## Previous High-Performing Content
{previous_content}

Create a complete draft including:
1. Headline options (3 variations)
2. Introduction hook
3. Main content sections
4. Call to action
5. Meta description"""

    LEAD_OUTREACH_SYSTEM = """You are a lead generation specialist. Your job is to:
1. Analyze lead lists and prioritize outreach
2. Craft personalized email sequences
3. Track outreach metrics and optimize
4. Identify high-value prospects

Focus on quality over quantity. Personalization is key.
Reference specific details about the prospect's company or role."""

    LEAD_OUTREACH_TEMPLATE = """Analyze leads and prepare outreach for {client}:

## Target Persona
{persona}

## Product/Service Value Proposition
{value_prop}

## Lead List
{leads}

## Previous Outreach Performance
{outreach_stats}

Provide:
1. Lead prioritization (A/B/C tier with reasoning)
2. Personalized first-touch email for top 5 leads
3. Follow-up sequence recommendations
4. Suggested subject lines with A/B variants"""

    AD_MANAGEMENT_SYSTEM = """You are a paid advertising specialist. Your job is to:
1. Monitor campaign performance across platforms
2. Identify underperforming ads and optimization opportunities
3. Recommend budget allocation changes
4. Generate new ad creative variations

Focus on ROAS, CAC, and conversion metrics.
Be specific about which campaigns need attention and why."""

    AD_MANAGEMENT_TEMPLATE = """Review ad performance for {client}:

## Campaign Summary
{campaign_data}

## Performance by Ad Set
{adset_data}

## Creative Performance
{creative_data}

## Budget Allocation
{budget_data}

Provide:
1. **Performance Summary** (key metrics vs. benchmarks)
2. **Issues Identified** (underperforming ads, budget waste)
3. **Optimization Actions** (specific changes to make)
4. **Creative Recommendations** (new angles to test)
5. **Budget Reallocation** (if needed)"""

    SEO_OPTIMIZATION_SYSTEM = """You are an SEO specialist. Your job is to:
1. Identify ranking opportunities from Search Console data
2. Analyze competitor SERP positions
3. Recommend technical and content optimizations
4. Track progress on key target keywords

Focus on quick wins: queries in positions 4-20 with high impressions.
Prioritize actions by potential traffic impact."""

    SEO_OPTIMIZATION_TEMPLATE = """Analyze SEO opportunities for {client}:

## Current Rankings (Position 4-20, High Impressions)
{ranking_opportunities}

## Technical Issues
{technical_issues}

## Content Gaps
{content_gaps}

## Competitor Analysis
{competitor_data}

Provide:
1. **Quick Wins** (actions for immediate ranking improvements)
2. **Content Priorities** (new/updated content needed)
3. **Technical Fixes** (issues to address)
4. **Keyword Strategy** (target keywords to focus on)"""

    WEEKLY_REPORT_SYSTEM = """You are a marketing strategist preparing a weekly executive report. Your job is to:
1. Synthesize data across all marketing channels
2. Evaluate progress toward goals
3. Identify strategic opportunities and threats
4. Provide high-level recommendations

Write for a busy executive. Lead with insights, not data.
Be honest about what's working and what isn't."""

    WEEKLY_REPORT_TEMPLATE = """Create weekly marketing report for {client}:

## Week of {date_range}

### Traffic & Engagement
{traffic_data}

### Campaign Performance
{campaign_data}

### Content Performance
{content_data}

### Lead Generation
{lead_data}

### Goals Progress
{goals_data}

Generate a comprehensive weekly report including:
1. **Executive Summary** (3-5 sentences)
2. **Key Wins** (what worked well)
3. **Challenges** (what needs improvement)
4. **Channel Performance** (by channel breakdown)
5. **Next Week Priorities** (top 3 focus areas)
6. **Strategic Recommendations** (longer-term considerations)"""

    @classmethod
    def get_prompt(
        cls,
        task_type: str,
        **kwargs
    ) -> tuple[str, str]:
        """
        Get system and user prompts for a task type.

        Args:
            task_type: Type of task
            **kwargs: Template variables

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        prompts = {
            "daily_analytics": (cls.DAILY_ANALYTICS_SYSTEM, cls.DAILY_ANALYTICS_TEMPLATE),
            "content_pipeline": (cls.CONTENT_PIPELINE_SYSTEM, cls.CONTENT_PIPELINE_TEMPLATE),
            "lead_outreach": (cls.LEAD_OUTREACH_SYSTEM, cls.LEAD_OUTREACH_TEMPLATE),
            "ad_management": (cls.AD_MANAGEMENT_SYSTEM, cls.AD_MANAGEMENT_TEMPLATE),
            "seo_optimization": (cls.SEO_OPTIMIZATION_SYSTEM, cls.SEO_OPTIMIZATION_TEMPLATE),
            "weekly_report": (cls.WEEKLY_REPORT_SYSTEM, cls.WEEKLY_REPORT_TEMPLATE),
        }

        if task_type not in prompts:
            raise ValueError(f"Unknown task type: {task_type}")

        system, template = prompts[task_type]

        # Format template with kwargs
        user_prompt = template.format(**kwargs) if kwargs else template

        return system, user_prompt
