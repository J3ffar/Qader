// Based on the API documentation

export interface ContentImage {
  id: number;
  page: number | null;
  slug: string;
  name: string;
  image_url: string;
  alt_text: string;
  uploaded_by_name: string;
  created_at: string;
}

export interface StructuredContentValue {
  admin_title: string;
  type: "text" | "textarea" | "html" | "image" | "repeater" | "url";
  value: any;
}

export interface Page {
  id: number;
  slug: string;
  title: string;
  content: string | null;
  content_structured: Record<string, StructuredContentValue> | null;
  icon_class: string | null;
  is_published: boolean;
  images: ContentImage[];
  created_at: string;
  updated_at: string;
}

export interface PageListItem {
  id: number;
  slug: string;
  title: string;
  is_published: boolean;
  updated_at: string;
}

export interface UpdatePagePayload {
  title?: string;
  is_published?: boolean;
  content?: string | null;
  content_structured?: Record<
    string,
    Pick<StructuredContentValue, "value">
  > | null;
}

export interface UploadImagePayload {
  image: File;
  name: string;
  alt_text: string;
  slug?: string;
}

// ... other types for FAQ, Homepage, etc. can be added here.

export interface HomepageFeatureCard {
  id: number;
  title: string;
  text: string;
  svg_image: string | null;
  icon_class: string | null;
  order: number;
  is_active: boolean;
}

export interface HomepageStatistic {
  id: number;
  label: string;
  value: string;
  icon_class: string | null;
  order: number;
  is_active: boolean;
}
