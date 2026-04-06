"""Website operations — SEO elements, schema markup, trust blocks, linking, and page builders.

Provides generators for on-page SEO elements, schema.org structured data,
trust/social-proof HTML blocks, internal linking recommendations, and
complete page structure builders for local service businesses.
All generators accept BusinessProfile-style dicts and produce structured
output ready for page injection via CMS connectors.
"""

from .seo_elements import (
    # Constants
    TITLE_MAX_CHARS,
    TITLE_MIN_CHARS,
    META_DESC_MAX_CHARS,
    META_DESC_MIN_CHARS,
    SCHEMA_CONTEXT,
    PAGE_TYPES,
    # Title / Meta
    generate_title_tag,
    generate_meta_description,
    generate_og_tags,
    # Schema markup
    generate_local_business_schema,
    generate_service_schema,
    generate_product_schema,
    generate_faq_schema,
    generate_howto_schema,
    generate_organization_schema,
    generate_review_schema,
    # Trust blocks
    generate_trust_block,
    generate_credentials_section,
    generate_social_proof_bar,
    # Internal linking
    recommend_internal_links,
    analyze_site_linking_opportunities,
)

from .local_service_pages import (
    # Models
    PageSection,
    PageStructure,
    # Builders
    build_homepage,
    build_service_page,
    build_service_area_page,
    build_contact_page,
    # Constants
    VALID_SECTION_TYPES,
)

__all__ = [
    # SEO elements — constants
    "TITLE_MAX_CHARS",
    "TITLE_MIN_CHARS",
    "META_DESC_MAX_CHARS",
    "META_DESC_MIN_CHARS",
    "SCHEMA_CONTEXT",
    "PAGE_TYPES",
    # SEO elements — title / meta
    "generate_title_tag",
    "generate_meta_description",
    "generate_og_tags",
    # SEO elements — schema markup
    "generate_local_business_schema",
    "generate_service_schema",
    "generate_product_schema",
    "generate_faq_schema",
    "generate_howto_schema",
    "generate_organization_schema",
    "generate_review_schema",
    # SEO elements — trust blocks
    "generate_trust_block",
    "generate_credentials_section",
    "generate_social_proof_bar",
    # SEO elements — internal linking
    "recommend_internal_links",
    "analyze_site_linking_opportunities",
    # Local service page builders — models
    "PageSection",
    "PageStructure",
    # Local service page builders — builders
    "build_homepage",
    "build_service_page",
    "build_service_area_page",
    "build_contact_page",
    # Local service page builders — constants
    "VALID_SECTION_TYPES",
]
