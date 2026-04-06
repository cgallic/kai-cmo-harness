# Task 039: Build social platform connectors

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 7. Social Operations
**Priority:** P1
**Depends on:** None
**Estimated complexity:** Large

## Context

The Kai Marketing OS needs to publish, schedule, and monitor social media content across all major platforms. Before any social content type system, scheduling queue, or caption engine can exist, there must be a uniform connector layer that abstracts each platform's API into a common interface. This is the foundation of Workstream 7 — every downstream social feature (Tasks 040-043) depends on these connectors existing and exposing a consistent contract.

Each connector handles authentication, rate limiting, media uploads, and platform-specific quirks while presenting a clean, identical interface to the rest of the system.

## Scope

Create the `kai/connectors/social/` package with a base abstract connector and five platform-specific implementations (Facebook, Instagram, LinkedIn, TikTok, YouTube). Each connector is a stub that defines the full interface and data flow without requiring live API credentials.

## Detailed Requirements

### File: `kai/connectors/social/__init__.py`

- Module docstring: "Social platform connectors — uniform interface for publishing, scheduling, and analytics across social media platforms."
- Import and re-export all connector classes
- Export a `PLATFORM_REGISTRY: Dict[str, Type[SocialConnector]]` mapping platform name strings to their connector class (e.g., `{"facebook": FacebookConnector, "instagram": InstagramConnector, ...}`)
- Export `get_connector(platform: str, config: dict) -> SocialConnector` factory function that looks up the registry and instantiates
- `__all__` listing all public names

### File: `kai/connectors/social/base.py`

Use the same Pydantic import fallback pattern from `gateway/models.py`. Use `abc.ABC` and `abc.abstractmethod` for the abstract base.

**Model: SocialConnectorConfig**
- `platform: str` — platform name (facebook, instagram, linkedin, tiktok, youtube)
- `api_key: Optional[str]` — API key if applicable
- `api_secret: Optional[str]` — API secret if applicable
- `access_token: Optional[str]` — OAuth access token
- `refresh_token: Optional[str]` — OAuth refresh token
- `token_expiry: Optional[str]` — ISO timestamp when access token expires
- `page_id: Optional[str]` — platform-specific page/account identifier
- `sandbox_mode: bool = True` — when True, no real API calls are made
- `rate_limit_rpm: int = 60` — requests per minute cap
- `metadata: Dict[str, Any]` — catch-all for platform-specific config, default empty dict

**Model: SocialPost**
- `id: Optional[str]` — platform-assigned post ID (None before publishing)
- `platform: str` — which platform this post targets
- `content_text: str` — the caption/text body
- `media_urls: List[str]` — URLs or local paths to media files, default empty list
- `media_type: Optional[str]` — one of: "image", "video", "carousel", "reel", "story", "short", None
- `link_url: Optional[str]` — URL to include in the post (if supported)
- `hashtags: List[str]` — hashtags to include, default empty list
- `location_tag: Optional[str]` — location/geo tag identifier
- `schedule_time: Optional[str]` — ISO timestamp for scheduled publishing (None = publish immediately)
- `status: str` — one of: "draft", "pending_approval", "approved", "scheduled", "published", "failed", default "draft"
- `published_at: Optional[str]` — ISO timestamp when actually published
- `published_url: Optional[str]` — URL to the live post
- `error_message: Optional[str]` — error details if status is "failed"
- `metadata: Dict[str, Any]` — default empty dict

**Model: SocialMetrics**
- `post_id: str` — the post this metrics object refers to
- `platform: str`
- `impressions: int = 0`
- `reach: int = 0`
- `likes: int = 0`
- `comments: int = 0`
- `shares: int = 0`
- `saves: int = 0`
- `clicks: int = 0`
- `video_views: int = 0`
- `engagement_rate: float = 0.0` — calculated as (likes+comments+shares+saves) / reach
- `fetched_at: Optional[str]` — ISO timestamp when metrics were last pulled

**Model: AudienceInsights**
- `platform: str`
- `total_followers: int = 0`
- `follower_growth_30d: int = 0`
- `top_locations: List[Dict[str, Any]]` — list of {location, percentage}, default empty list
- `age_gender_breakdown: List[Dict[str, Any]]` — list of {age_range, gender, percentage}, default empty list
- `active_hours: List[Dict[str, Any]]` — list of {day, hour, engagement_level}, default empty list
- `fetched_at: Optional[str]`

**Model: MediaRequirements**
- `platform: str`
- `max_image_size_mb: float`
- `max_video_size_mb: float`
- `max_video_duration_seconds: int`
- `supported_image_formats: List[str]` — e.g., ["jpg", "png", "webp"]
- `supported_video_formats: List[str]` — e.g., ["mp4", "mov"]
- `aspect_ratios: Dict[str, str]` — mapping content type to recommended ratio, e.g., {"feed": "1:1", "story": "9:16"}
- `max_caption_length: int`
- `max_hashtags: int`

**Model: RateLimitState**
- `requests_made: int = 0`
- `requests_remaining: int = 60`
- `window_reset_at: Optional[str]` — ISO timestamp when the rate limit window resets
- `is_throttled: bool = False`

**Abstract class: SocialConnector(ABC)**
- `__init__(self, config: SocialConnectorConfig)` — store config, initialize `_rate_limit: RateLimitState`
- `platform_name: str` — abstract property returning the platform identifier string
- `media_requirements: MediaRequirements` — abstract property returning platform-specific media constraints

Methods (all abstract):
- `connect(self) -> bool` — test the connection / validate credentials. Return True if connected.
- `refresh_auth(self) -> bool` — refresh OAuth token if expired. Return True if refreshed.
- `get_profile(self) -> Dict[str, Any]` — return the connected page/account profile info
- `get_posts(self, limit: int = 20, cursor: Optional[str] = None) -> List[SocialPost]` — fetch recent posts with pagination
- `create_post(self, post: SocialPost) -> SocialPost` — publish or schedule a post. Return updated post with id and status.
- `update_post(self, post_id: str, updates: Dict[str, Any]) -> SocialPost` — update an existing post (if platform allows)
- `delete_post(self, post_id: str) -> bool` — delete a post. Return True if successful.
- `get_metrics(self, post_id: str) -> SocialMetrics` — fetch engagement metrics for a specific post
- `get_audience_insights(self) -> AudienceInsights` — fetch audience demographics and behavior data
- `upload_media(self, file_path: str, media_type: str) -> str` — upload a media file and return a platform media reference/ID

Concrete helper methods (not abstract):
- `_check_rate_limit(self) -> bool` — check if a request can be made without exceeding rate limits. If throttled, return False.
- `_record_request(self)` — increment `_rate_limit.requests_made`, update remaining
- `_validate_post(self, post: SocialPost) -> List[str]` — validate a post against `media_requirements` (caption length, hashtag count, media format). Return list of validation error strings (empty = valid).
- `_is_sandbox(self) -> bool` — return `self.config.sandbox_mode`
- `_sandbox_response(self, method_name: str, **kwargs) -> Dict[str, Any]` — return a mock response dict for sandbox mode with `{"sandbox": True, "method": method_name, **kwargs}`

### File: `kai/connectors/social/facebook.py`

**Class: FacebookConnector(SocialConnector)**
- `platform_name` property returns `"facebook"`
- `media_requirements` property returns MediaRequirements with:
  - max_image_size_mb: 10.0
  - max_video_size_mb: 4096.0 (4GB)
  - max_video_duration_seconds: 14400 (240 min)
  - supported_image_formats: ["jpg", "png", "bmp", "gif", "tiff"]
  - supported_video_formats: ["mp4", "mov", "avi"]
  - aspect_ratios: {"feed": "flexible", "story": "9:16", "reel": "9:16"}
  - max_caption_length: 63206
  - max_hashtags: 30
- Graph API version constant: `API_VERSION = "v19.0"`
- Base URL constant: `BASE_URL = "https://graph.facebook.com/{API_VERSION}"`
- All methods: check `_is_sandbox()` first and return `_sandbox_response()` if True
- `connect()`: validate that config has `access_token` and `page_id`, attempt to fetch page info via `/{page_id}?fields=name,id,fan_count`
- `create_post()`: construct the Graph API `/{page_id}/feed` payload. Handle text-only, single image (`/{page_id}/photos`), video (`/{page_id}/videos`), and link posts. Include scheduling via `published=false` + `scheduled_publish_time` if `schedule_time` is set.
- `get_metrics()`: fetch from `/{post_id}/insights` with metrics: `post_impressions`, `post_impressions_unique`, `post_engaged_users`, `post_clicks`
- `get_audience_insights()`: fetch from `/{page_id}/insights` with `page_fans_city`, `page_fans_gender_age`, `page_fans_online`
- Include `_build_headers(self) -> Dict[str, str]` helper that returns `{"Authorization": f"Bearer {self.config.access_token}"}`

### File: `kai/connectors/social/instagram.py`

**Class: InstagramConnector(SocialConnector)**
- `platform_name` returns `"instagram"`
- `media_requirements`:
  - max_image_size_mb: 8.0
  - max_video_size_mb: 4096.0
  - max_video_duration_seconds: 5400 (90 min for IGTV/Reels, 60 for feed, 15 for stories)
  - supported_image_formats: ["jpg", "png"]
  - supported_video_formats: ["mp4", "mov"]
  - aspect_ratios: {"feed_square": "1:1", "feed_portrait": "4:5", "feed_landscape": "1.91:1", "story": "9:16", "reel": "9:16"}
  - max_caption_length: 2200
  - max_hashtags: 30
- Uses Instagram Graph API (through Facebook Graph API)
- `create_post()`: handle three flows:
  1. **Single image feed post**: POST to `/{ig_user_id}/media` with `image_url` + `caption`, then POST to `/{ig_user_id}/media_publish` with the `creation_id`
  2. **Carousel**: POST multiple items to `/{ig_user_id}/media` with `is_carousel_item=true`, then POST to `/{ig_user_id}/media` with `media_type=CAROUSEL` + `children`, then publish
  3. **Reel**: POST to `/{ig_user_id}/media` with `video_url` + `media_type=REELS` + `caption`, then publish
- `get_metrics()`: fetch `/{media_id}/insights` with metrics: `impressions`, `reach`, `engagement`, `saved`, `video_views` (for reels)
- `_get_hashtag_id(self, hashtag: str) -> Optional[str]` — helper to search for hashtag ID via `ig_hashtag_search`
- `_get_recent_hashtag_media(self, hashtag_id: str, limit: int = 25) -> List[Dict]` — helper for hashtag research

### File: `kai/connectors/social/linkedin.py`

**Class: LinkedInConnector(SocialConnector)**
- `platform_name` returns `"linkedin"`
- `media_requirements`:
  - max_image_size_mb: 10.0
  - max_video_size_mb: 5120.0 (5GB)
  - max_video_duration_seconds: 600 (10 min)
  - supported_image_formats: ["jpg", "png", "gif"]
  - supported_video_formats: ["mp4"]
  - aspect_ratios: {"feed": "flexible", "video": "16:9 or 1:1"}
  - max_caption_length: 3000
  - max_hashtags: 5 (recommended; technically 30 allowed)
- Uses LinkedIn Marketing API v2
- `create_post()`:
  - Text post: POST to `/ugcPosts` with `shareCommentary` and `shareMediaCategory=NONE`
  - Image post: first register upload via `/assets?action=registerUpload`, upload binary, then POST to `/ugcPosts` with `shareMediaCategory=IMAGE`
  - Article/link post: POST with `shareMediaCategory=ARTICLE` and `originalUrl`
  - Video: register upload, upload chunks, then POST with `shareMediaCategory=VIDEO`
- Company page vs personal profile: use `config.page_id` to determine if posting as organization (`urn:li:organization:{id}`) or person (`urn:li:person:{id}`)
- `get_metrics()`: fetch from `/organizationalEntityShareStatistics` with `shares` filter
- `get_audience_insights()`: fetch from `/organizationalEntityFollowerStatistics` — follower counts, demographics by industry/function/seniority

### File: `kai/connectors/social/tiktok.py`

**Class: TikTokConnector(SocialConnector)**
- `platform_name` returns `"tiktok"`
- `media_requirements`:
  - max_image_size_mb: 10.0 (for photo mode)
  - max_video_size_mb: 4096.0
  - max_video_duration_seconds: 600 (10 min)
  - supported_image_formats: ["jpg", "png", "webp"]
  - supported_video_formats: ["mp4", "mov", "webm"]
  - aspect_ratios: {"video": "9:16"}
  - max_caption_length: 2200
  - max_hashtags: 100 (but 3-5 recommended)
- Uses TikTok Business API v2
- `create_post()`:
  - Video post: first call `/post/publish/video/init/` to get `publish_id`, upload video to provided URL, then check status via `/post/publish/status/fetch/`
  - Photo mode: call `/post/publish/content/init/` with `post_mode=DIRECT_POST` and `media_type=PHOTO`
  - Set `privacy_level` from config (PUBLIC_TO_EVERYONE, MUTUAL_FOLLOW_FRIENDS, FOLLOWER_OF_CREATOR, SELF_ONLY)
  - Support `disable_comment`, `disable_duet`, `disable_stitch` flags from post metadata
- `get_metrics()`: fetch from `/video/query/` — views, likes, comments, shares, average_watch_time, video_duration
- `get_audience_insights()`: fetch from `/business/get/` — follower demographics
- `_get_trending_sounds(self, limit: int = 20) -> List[Dict[str, Any]]` — stub for fetching trending audio/sounds

### File: `kai/connectors/social/youtube.py`

**Class: YouTubeConnector(SocialConnector)**
- `platform_name` returns `"youtube"`
- `media_requirements`:
  - max_image_size_mb: 2.0 (thumbnail)
  - max_video_size_mb: 131072.0 (128GB)
  - max_video_duration_seconds: 43200 (12 hours)
  - supported_image_formats: ["jpg", "png"]
  - supported_video_formats: ["mp4", "mov", "avi", "wmv", "flv", "webm"]
  - aspect_ratios: {"video": "16:9", "short": "9:16"}
  - max_caption_length: 5000 (description)
  - max_hashtags: 15
- Uses YouTube Data API v3
- `__init__` additional attribute: `_is_shorts_focus: bool = True` (Kai focuses on Shorts for most local businesses)
- `create_post()`:
  - Standard video: resumable upload to `https://www.googleapis.com/upload/youtube/v3/videos`, set `snippet` (title, description, tags, categoryId), `status` (privacyStatus, publishAt for scheduling, selfDeclaredMadeForKids)
  - Short: same upload flow but title includes `#Shorts`, video is vertical 9:16, max 60 seconds
  - Set `notifySubscribers` from config
- `get_metrics()`: fetch from `youtube.videos().list(part="statistics")` — viewCount, likeCount, commentCount, favoriteCount
- `get_audience_insights()`: fetch from `youtube.channels().list(part="statistics")` — subscriberCount, videoCount, viewCount; plus `youtubeAnalytics.reports().query()` for demographics
- `upload_media()`: implement resumable upload protocol — initiate with POST, upload chunks, handle resume on failure
- `_set_thumbnail(self, video_id: str, thumbnail_path: str) -> bool` — set custom thumbnail via `youtube.thumbnails().set()`

### General requirements for ALL connector files:

1. Every file starts with a module docstring explaining the platform and API version
2. Use `from __future__ import annotations` at the top
3. Import `logging` and create a module-level logger: `logger = logging.getLogger(__name__)`
4. Every API call method must: (a) check `_is_sandbox()`, (b) check `_check_rate_limit()`, (c) record the request via `_record_request()`, (d) wrap actual API call in try/except with logging
5. Every connector stores a `_connected: bool = False` flag, set to True on successful `connect()`
6. All mutating methods (create_post, update_post, delete_post) must check `_connected` and raise `ConnectionError` if not connected
7. Type annotations on all methods and return values
8. No actual HTTP library imports (no requests, httpx, etc.) — use a placeholder `self._api_call(method, url, **kwargs)` method that in production would use the configured HTTP client but for now just raises `NotImplementedError("Live API calls not yet implemented — use sandbox mode")` when not in sandbox mode

## Output Files

- `kai/connectors/__init__.py` (create, empty or minimal)
- `kai/connectors/social/__init__.py`
- `kai/connectors/social/base.py`
- `kai/connectors/social/facebook.py`
- `kai/connectors/social/instagram.py`
- `kai/connectors/social/linkedin.py`
- `kai/connectors/social/tiktok.py`
- `kai/connectors/social/youtube.py`

## Acceptance Criteria

- [ ] `kai/connectors/social/base.py` contains SocialConnectorConfig, SocialPost, SocialMetrics, AudienceInsights, MediaRequirements, RateLimitState models with all fields listed above
- [ ] SocialConnector abstract class has all 10 abstract methods with correct signatures
- [ ] SocialConnector has all 5 concrete helper methods implemented
- [ ] All 5 platform connectors (Facebook, Instagram, LinkedIn, TikTok, YouTube) extend SocialConnector
- [ ] Each connector defines correct `platform_name` property and `media_requirements` with accurate platform-specific values
- [ ] Each connector implements all abstract methods with platform-appropriate logic and API endpoint references
- [ ] All connectors check sandbox mode before any API call
- [ ] All connectors check rate limits before any API call
- [ ] All connectors check `_connected` before mutating operations
- [ ] Instagram connector handles the two-step publish flow (create container, then publish)
- [ ] LinkedIn connector handles both company page and personal profile posting
- [ ] TikTok connector includes trending sounds stub
- [ ] YouTube connector includes Shorts-specific logic and resumable upload stub
- [ ] `kai/connectors/social/__init__.py` exports `PLATFORM_REGISTRY` and `get_connector` factory
- [ ] No live HTTP imports — all connectors use the `_api_call` placeholder pattern
- [ ] Pydantic import fallback pattern matches `gateway/models.py`

## Reference Materials

- `gateway/models.py` — Pydantic import fallback pattern (lines 1-30)
- `kai/runtime/actions.py` — existing action store patterns and ID generation (lines 1-50)
- `knowledge/channels/instagram.md` — Instagram-specific marketing guidance
- `knowledge/channels/linkedin-articles.md` — LinkedIn content guidance
- `knowledge/channels/tiktok-algorithm.md` — TikTok algorithm and content strategy
- `knowledge/channels/youtube.md` — YouTube content guidance
- `knowledge/channels/meta-advertising.md` — Meta platform guidance
- `knowledge/playbooks/social-media-strategy.md` — overall social strategy
- `CLAUDE.md` — full project context
