# Meta Ads API — Execution Reference

*Harness reference for creating and managing Meta ad campaigns via the Marketing API. Covers campaign/adset/ad creation, field names, targeting templates, and common gotchas discovered in production.*

---

## 1. API Basics

**Base URL:** `https://graph.facebook.com/v21.0`

**Authentication:** All requests require a valid access token.

```bash
# Extract token from .env.local (Windows-safe — no `source`)
META_TOKEN=$(grep '^META_ACCESS_TOKEN=' .env.local | cut -d= -f2-)
AD_ACCOUNT_ID=$(grep '^META_AD_ACCOUNT_ID=' .env.local | cut -d= -f2-)
```

> **Windows/.env.local rule:** Never use `source .env.local` — placeholder values and special characters break bash. Always use `grep` extraction.

---

## 2. Campaign Creation Flow

Three-step process. Each step requires the ID from the previous step.

```
1. Create Campaign  → returns campaign_id
2. Create Ad Set    → returns adset_id (needs campaign_id)
3. Create Ad        → returns ad_id (needs adset_id + creative)
```

### Step 1: Create Campaign

```bash
curl -X POST "https://graph.facebook.com/v21.0/act_${AD_ACCOUNT_ID}/campaigns" \
  -d "name=Campaign Name" \
  -d "objective=OUTCOME_LEADS" \
  -d "status=PAUSED" \
  -d "special_ad_categories=[]" \
  -d "access_token=${META_TOKEN}"
```

**Required fields:**
| Field | Type | Notes |
|-------|------|-------|
| `name` | string | Campaign name |
| `objective` | enum | `OUTCOME_LEADS`, `OUTCOME_SALES`, `OUTCOME_TRAFFIC`, `OUTCOME_AWARENESS`, `OUTCOME_ENGAGEMENT`, `OUTCOME_APP_PROMOTION` |
| `status` | enum | `PAUSED` (recommended — review before activating) or `ACTIVE` |
| `special_ad_categories` | array | `[]` or `["HOUSING"]`, `["EMPLOYMENT"]`, `["CREDIT"]`, `["ISSUES_ELECTIONS_POLITICS"]` |

### Step 2: Create Ad Set

```bash
curl -X POST "https://graph.facebook.com/v21.0/act_${AD_ACCOUNT_ID}/adsets" \
  -d "name=Ad Set Name" \
  -d "campaign_id=${CAMPAIGN_ID}" \
  -d "daily_budget=2000" \
  -d "billing_event=IMPRESSIONS" \
  -d "optimization_goal=LEAD_GENERATION" \
  -d "promoted_object={\"page_id\":\"${PAGE_ID}\"}" \
  -d "targeting={\"age_min\":25,\"age_max\":65,\"geo_locations\":{\"countries\":[\"US\"]},\"targeting_automation\":{\"advantage_audience\":1}}" \
  -d "status=PAUSED" \
  -d "access_token=${META_TOKEN}"
```

**Required fields:**
| Field | Type | Notes |
|-------|------|-------|
| `name` | string | Ad set name |
| `campaign_id` | string | From Step 1 |
| `daily_budget` | int | **In cents** — `2000` = $20.00/day |
| `billing_event` | enum | `IMPRESSIONS` (standard) |
| `optimization_goal` | enum | `LEAD_GENERATION`, `OFFSITE_CONVERSIONS`, `LINK_CLICKS`, `REACH`, `IMPRESSIONS` |
| `promoted_object` | object | `{"page_id":"..."}` for lead gen; `{"pixel_id":"...","custom_event_type":"..."}` for conversions |
| `targeting` | object | See Section 4 |
| `status` | enum | `PAUSED` or `ACTIVE` |

> **Budget is in cents.** `daily_budget=5000` means $50/day. This is a common mistake.

### Step 3: Create Ad

```bash
curl -X POST "https://graph.facebook.com/v21.0/act_${AD_ACCOUNT_ID}/ads" \
  -d "name=Ad Name" \
  -d "adset_id=${ADSET_ID}" \
  -d "creative={\"object_story_spec\":{\"page_id\":\"${PAGE_ID}\",\"instagram_user_id\":\"${IG_ACCOUNT_ID}\",\"link_data\":{\"link\":\"https://example.com\",\"message\":\"Primary text here\",\"name\":\"Headline here\",\"description\":\"Link description\",\"call_to_action\":{\"type\":\"LEARN_MORE\"},\"image_hash\":\"${IMAGE_HASH}\"}}}" \
  -d "status=PAUSED" \
  -d "access_token=${META_TOKEN}"
```

**Required fields:**
| Field | Type | Notes |
|-------|------|-------|
| `name` | string | Ad name |
| `adset_id` | string | From Step 2 |
| `creative` | object | Inline creative with `object_story_spec` |
| `status` | enum | `PAUSED` or `ACTIVE` |

---

## 3. Creative `object_story_spec` Fields

> **CRITICAL: The field is `instagram_user_id`, NOT `instagram_actor_id`.** The API documentation and many tutorials reference `instagram_actor_id` but the working field name in v21.0 is `instagram_user_id`. Using the wrong name causes a silent failure where the ad creates but cannot serve on Instagram placements.

### Image Ad (link_data)

```json
{
  "object_story_spec": {
    "page_id": "FACEBOOK_PAGE_ID",
    "instagram_user_id": "INSTAGRAM_ACCOUNT_ID",
    "link_data": {
      "link": "https://landing-page.com",
      "message": "Primary text (body copy)",
      "name": "Headline text",
      "description": "Link description text",
      "call_to_action": {
        "type": "LEARN_MORE"
      },
      "image_hash": "IMAGE_HASH_FROM_UPLOAD"
    }
  }
}
```

### Video Ad (video_data)

```json
{
  "object_story_spec": {
    "page_id": "FACEBOOK_PAGE_ID",
    "instagram_user_id": "INSTAGRAM_ACCOUNT_ID",
    "video_data": {
      "video_id": "VIDEO_ID_FROM_LIBRARY",
      "message": "Primary text (body copy)",
      "title": "Headline text",
      "call_to_action": {
        "type": "LEARN_MORE",
        "value": {
          "link": "https://landing-page.com"
        }
      },
      "image_hash": "THUMBNAIL_IMAGE_HASH"
    }
  }
}
```

> **Video ads require `video_id`, NOT `video_url`.** You must upload the video first or reference an existing video from the ad account's video library. See Section 5.

### CTA Types

Common `call_to_action.type` values:
- `LEARN_MORE` — generic, safe default
- `SIGN_UP` — registration flows
- `GET_QUOTE` — service businesses
- `BOOK_NOW` — appointment-based
- `CONTACT_US` — lead gen
- `SHOP_NOW` — ecommerce
- `WATCH_MORE` — video content
- `DOWNLOAD` — app/resource
- `SUBSCRIBE` — newsletter/SaaS

---

## 4. Targeting Spec Templates

### Basic Targeting (Advantage+ recommended)

```json
{
  "age_min": 25,
  "age_max": 65,
  "geo_locations": {
    "countries": ["US"]
  },
  "targeting_automation": {
    "advantage_audience": 1
  }
}
```

### Interest-Based Targeting

```json
{
  "age_min": 25,
  "age_max": 55,
  "genders": [0],
  "geo_locations": {
    "countries": ["US"],
    "regions": [{"key": "3847"}],
    "cities": [{"key": "2420379", "radius": 25, "distance_unit": "mile"}]
  },
  "interests": [
    {"id": "6003139266461", "name": "Small business"},
    {"id": "6003384248805", "name": "Entrepreneurship"}
  ],
  "targeting_automation": {
    "advantage_audience": 1
  }
}
```

> **Gender values:** `0` = all, `1` = male, `2` = female

### Custom Audience Targeting

```json
{
  "age_min": 18,
  "age_max": 65,
  "geo_locations": {
    "countries": ["US"]
  },
  "custom_audiences": [
    {"id": "CUSTOM_AUDIENCE_ID"}
  ]
}
```

### Interest Search

To find valid interest IDs:

```bash
curl "https://graph.facebook.com/v21.0/search?type=adinterest&q=small+business&access_token=${META_TOKEN}"
```

---

## 5. Video Library Management

### List Videos in Ad Account

**Always verify video IDs before creating video ads.** Video IDs are long numeric strings where a single digit difference means a completely different (or nonexistent) video.

```bash
curl "https://graph.facebook.com/v21.0/act_${AD_ACCOUNT_ID}/advideos?fields=id,title,created_time,length,thumbnails&limit=20&access_token=${META_TOKEN}"
```

### Upload a Video

```bash
curl -X POST "https://graph.facebook.com/v21.0/act_${AD_ACCOUNT_ID}/advideos" \
  -F "source=@/path/to/video.mp4" \
  -F "title=Ad Video Title" \
  -F "access_token=${META_TOKEN}"
```

### Upload an Image

```bash
curl -X POST "https://graph.facebook.com/v21.0/act_${AD_ACCOUNT_ID}/adimages" \
  -F "filename=@/path/to/image.jpg" \
  -F "access_token=${META_TOKEN}"
```

Returns `image_hash` for use in creative `link_data`.

---

## 6. Reading Insights (Performance Data)

### Campaign-Level

```bash
curl "https://graph.facebook.com/v21.0/${CAMPAIGN_ID}/insights?fields=campaign_name,impressions,clicks,spend,actions,cost_per_action_type,ctr,cpc&date_preset=last_30d&access_token=${META_TOKEN}"
```

### Ad Set-Level

```bash
curl "https://graph.facebook.com/v21.0/${ADSET_ID}/insights?fields=adset_name,impressions,clicks,spend,actions,cost_per_action_type&date_preset=last_30d&access_token=${META_TOKEN}"
```

### Ad-Level (Individual Ads)

```bash
curl "https://graph.facebook.com/v21.0/${AD_ID}/insights?fields=ad_name,impressions,clicks,spend,actions,cost_per_action_type,ctr,cpc,video_avg_time_watched_actions,video_p25_watched_actions,video_p50_watched_actions,video_p75_watched_actions,video_p100_watched_actions&date_preset=last_30d&access_token=${META_TOKEN}"
```

### All Ads in Account with Insights

```bash
curl "https://graph.facebook.com/v21.0/act_${AD_ACCOUNT_ID}/ads?fields=name,status,effective_status,creative{id,name,object_story_spec},insights.date_preset(last_30d){impressions,clicks,spend,ctr,cpc,actions,cost_per_action_type}&limit=50&access_token=${META_TOKEN}"
```

### Daily Breakdown

Add `&time_increment=1` to any insights query for day-by-day data.

### Key Metrics to Pull

| Metric | Field | Benchmark (B2B SaaS) |
|--------|-------|---------------------|
| CTR | `ctr` | > 1% (good), > 2% (great) |
| CPC | `cpc` | < $3 (good), < $1.50 (great) |
| CPL | `cost_per_action_type` where `action_type=lead` | < $30 (good), < $15 (great) |
| Video 25% | `video_p25_watched_actions` | > 50% of impressions |
| Video 75% | `video_p75_watched_actions` | > 15% of impressions |

---

## 7. Listing Active Campaigns/Ads

### All Active Campaigns

```bash
curl "https://graph.facebook.com/v21.0/act_${AD_ACCOUNT_ID}/campaigns?fields=id,name,objective,status,daily_budget,lifetime_budget&filtering=[{\"field\":\"effective_status\",\"operator\":\"IN\",\"value\":[\"ACTIVE\"]}]&limit=50&access_token=${META_TOKEN}"
```

### All Active Ads with Creative Details

```bash
curl "https://graph.facebook.com/v21.0/act_${AD_ACCOUNT_ID}/ads?fields=id,name,status,effective_status,adset_id,campaign_id,creative{id,object_story_spec,url_tags}&filtering=[{\"field\":\"effective_status\",\"operator\":\"IN\",\"value\":[\"ACTIVE\"]}]&limit=100&access_token=${META_TOKEN}"
```

### Get Ad Creative by ID (Reverse Engineer Existing Ads)

```bash
curl "https://graph.facebook.com/v21.0/${CREATIVE_ID}?fields=id,name,object_story_spec,url_tags,asset_feed_spec&access_token=${META_TOKEN}"
```

> **Tip:** When in doubt about field names, pull an existing working creative and inspect its `object_story_spec` to see the correct field structure.

---

## 8. Updating and Pausing Ads

### Pause an Ad

```bash
curl -X POST "https://graph.facebook.com/v21.0/${AD_ID}" \
  -d "status=PAUSED" \
  -d "access_token=${META_TOKEN}"
```

### Update Ad Set Budget

```bash
curl -X POST "https://graph.facebook.com/v21.0/${ADSET_ID}" \
  -d "daily_budget=3000" \
  -d "access_token=${META_TOKEN}"
```

> Budget/schedule changes do NOT trigger re-review. Creative/targeting changes DO.

---

## 8.1 Creator And Automation API Pre-Flight

Before creating Meta ads from creator, UGC, or generated assets:

- Create ads in `PAUSED` state.
- Store `concept_id`, `asset_id`, and `utm_content` in the local upload sheet or payload log.
- Confirm Partnership Ads or whitelisting permission for creator content.
- Confirm usage-rights duration and expiration date.
- Confirm disclosure evidence and native paid-partnership label plan.
- Confirm AI/synthetic-media disclosure status where relevant.
- Attach the policy check and human approval ID to the audit log.

Do not activate Advantage+ or other automated delivery changes through API unless the decision memo names account state, enabled controls, known gaps, measurement method, and rollback plan.

---

## 9. Common Gotchas

### Field Name Mismatches

| Wrong (commonly referenced) | Correct (actually works) | Context |
|----|----|----|
| `instagram_actor_id` | `instagram_user_id` | `object_story_spec` in creative |
| `video_url` | `video_id` | `video_data` in creative |
| `budget` | `daily_budget` or `lifetime_budget` | Ad set level |

### Budget Units

- `daily_budget` and `lifetime_budget` are in **cents** (integer)
- `2000` = $20.00, `50000` = $500.00
- Minimum daily budget varies by country and optimization goal

### Status vs Effective Status

- `status` — what you set (ACTIVE, PAUSED)
- `effective_status` — actual delivery state (accounts for campaign/ad set/ad level status, review status, budget exhaustion)
- Always check `effective_status` to understand why an ad isn't delivering

### Rate Limits

- Standard: 200 calls per hour per ad account
- Batch requests available for bulk operations
- Use `?limit=` parameter to reduce number of requests needed

### JSON in curl

When passing JSON objects in curl `-d` flags, the entire value must be valid JSON. For complex objects, consider writing to a temp file:

```bash
# Write JSON to temp file to avoid shell escaping issues
node -e "
const payload = {
  name: 'Ad Name',
  adset_id: '${ADSET_ID}',
  creative: {
    object_story_spec: {
      page_id: '${PAGE_ID}',
      instagram_user_id: '${IG_ACCOUNT_ID}',
      link_data: {
        link: 'https://example.com',
        message: 'Primary text',
        name: 'Headline',
        call_to_action: { type: 'LEARN_MORE' },
        image_hash: '${IMAGE_HASH}'
      }
    }
  },
  status: 'PAUSED'
};
require('fs').writeFileSync('/tmp/ad_payload.json', JSON.stringify(payload));
"

curl -X POST "https://graph.facebook.com/v21.0/act_${AD_ACCOUNT_ID}/ads" \
  -H "Content-Type: application/json" \
  -d @/tmp/ad_payload.json \
  -d "access_token=${META_TOKEN}"
```

---

## 10. Environment Variable Reference

Expected `.env.local` keys for Meta API operations:

```
META_ACCESS_TOKEN=<long-lived user/system token>
META_AD_ACCOUNT_ID=<numeric, without act_ prefix>
META_PAGE_ID=<Facebook Page ID>
META_INSTAGRAM_USER_ID=<Instagram business account ID>
META_PIXEL_ID=<optional, for conversion tracking>
```

**Extraction pattern (Windows-safe):**

```bash
META_TOKEN=$(grep '^META_ACCESS_TOKEN=' .env.local | cut -d= -f2-)
AD_ACCOUNT_ID=$(grep '^META_AD_ACCOUNT_ID=' .env.local | cut -d= -f2-)
PAGE_ID=$(grep '^META_PAGE_ID=' .env.local | cut -d= -f2-)
IG_ACCOUNT_ID=$(grep '^META_INSTAGRAM_USER_ID=' .env.local | cut -d= -f2-)
```

---

*This reference reflects Meta Marketing API v21.0 behavior as of April 2026. Field names and endpoints may change between API versions.*
