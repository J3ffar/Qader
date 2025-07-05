// A generic type for a structured content item (text, image, etc.)
interface StructuredContentItem<T> {
  admin_title: string;
  type: string;
  value: T;
}

// A specific type for a repeater like reviews
interface RepeaterContentItem<T> {
  admin_title: string;
  type: "repeater";
  value: T[];
}

// Type for a single image from the ContentImage model
export interface ContentImage {
  id: number;
  slug: string;
  name: string;
  image: string | null;
  alt_text: string;
}

// A generic Page object from your backend
export interface Page<TContent> {
  slug: string;
  title: string;
  content: string | null;
  content_structured_resolved: TContent;
  images: ContentImage[];
  icon_class: string | null;
  updated_at: string;
}

/////// Part home page

export interface Feature {
  title: string;
  text: string;
  svg_image: string | null;
  icon_class: string | null;
}

export interface Statistic {
  label: string;
  value: string;
  icon_class: string | null;
}

export interface Review {
  name: string;
  title: string;
  quote: string;
}

// Specific structure for the 'homepage-intro' page's content
type IntroContent = {
  hero_title: StructuredContentItem<string>;
  hero_subtitle: StructuredContentItem<string>;
  main_hero_image: StructuredContentItem<string | null>;
  promo_icon: StructuredContentItem<string | null>;
};

// Specific structure for the 'homepage-praise' page's content
type PraiseContent = {
  section_title: StructuredContentItem<string>;
  section_subtitle: StructuredContentItem<string>;
  reviews: RepeaterContentItem<Review>;
};

// ADD this new type for the 'homepage-about-us' page's content
type AboutUsContent = {
  section_title: StructuredContentItem<string>;
  section_text: StructuredContentItem<string>;
  video_url: StructuredContentItem<string | null>;
  button_text: StructuredContentItem<string>;
  video_placeholder_image: StructuredContentItem<string | null>;
};

// Specific structure for the 'why-partner' page's content
type WhyPartnerContent = {
  section_title: StructuredContentItem<string>;
  section_subtitle: StructuredContentItem<string>;
  main_image: StructuredContentItem<string | null>;
};

// Specific structure for the 'homepage-cta' page's content
type CTAContent = {
  title: StructuredContentItem<string>;
  subtitle: StructuredContentItem<string>;
  button_text: StructuredContentItem<string>;
};

// The final, complete type for the homepage API response
export interface HomepageData {
  intro: Page<IntroContent> | null;
  praise: Page<PraiseContent> | null;
  about_us: Page<AboutUsContent> | null;
  features: Feature[] | null;
  statistics: Statistic[] | null;
  why_partner_text: Page<WhyPartnerContent> | null;
  call_to_action: Page<CTAContent> | null;
}

/////// Part for the page about us (story)

// Type for a single story card on the About Us page
export interface StoryCard {
  icon_type: "image" | "heroicon";
  icon_value: string | null;
  text: string;
}

// Type for a single point in the 'Why Different' list
export interface WhyDifferentPoint {
  point: string;
}

// The complete content structure for the About Us page
export type AboutPageContent = {
  hero_title: StructuredContentItem<string>;
  hero_subtitle: StructuredContentItem<string>;
  story_cards: RepeaterContentItem<StoryCard>;
  main_promo_image: StructuredContentItem<string | null>;
  why_different_title: StructuredContentItem<string>;
  why_different_points: RepeaterContentItem<WhyDifferentPoint>;
  why_different_image: StructuredContentItem<string | null>;
  mission_title: StructuredContentItem<string>;
  mission_text: StructuredContentItem<string>;
  mission_image: StructuredContentItem<string | null>;
};

/////// Part for the page Partners

// Type for a single Partner Category from the API
export interface PartnerCategory {
  id: number;
  name: string;
  description: string;
  icon_image: string | null;
  google_form_link: string;
}

// Updated content structure for the main Partners page
export type PartnersPageContent = {
  hero_title: StructuredContentItem<string>;
  hero_subtitle: StructuredContentItem<string>;
  why_partner_title: StructuredContentItem<string>; // ADDED
  why_partner_text: StructuredContentItem<string>; // ADDED
  why_partner_image: StructuredContentItem<string | null>;
};

// Updated type for the /partners API response
export interface PartnersPageData {
  partner_categories: PartnerCategory[];
  page_content: Page<PartnersPageContent> | null;
}
