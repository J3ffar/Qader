import { apiClient } from "./apiClient";
import type {
  AboutPageContent,
  FaqPageData,
  HomepageData,
  Page,
  PartnersPageData,
} from "@/types/api/content.types";

const defaultHomepageData: HomepageData = {
  intro: {
    slug: "homepage-intro",
    title:
      "عندك <span class='text-[#e78b48]'>اختبار قدرات؟</span> ومحتاج مساعدة!!",
    content: "منصتنا مخصصة لك، أنت في الطريق الصحيح.",
    content_structured_resolved: {
      hero_title: {
        admin_title: "...",
        type: "html",
        value:
          "عندك <span class='text-[#e78b48]'>اختبار قدرات؟</span> ومحتاج مساعدة!!",
      },
      hero_subtitle: {
        admin_title: "...",
        type: "textarea",
        value:
          "منصتنا مخصصة لك، أنت في الطريق الصحيح. اكتشف كيف يمكن لأدواتنا المبتكرة والمدعومة بالذكاء الاصطناعي أن تضعك على طريق النجاح.",
      },
      main_hero_image: {
        admin_title: "...",
        type: "image",
        value: "/images/photo.png",
      },
      promo_icon: {
        admin_title: "...",
        type: "image",
        value: "/images/container.png",
      },
    },
    images: [],
    icon_class: null,
    updated_at: new Date().toISOString(),
  },
  praise: {
    slug: "homepage-praise",
    title: "ماذا قالوا عنا؟",
    content: "آراء طلابنا هي شهادة نجاحنا.",
    content_structured_resolved: {
      section_title: {
        admin_title: "...",
        type: "html",
        value:
          "ماذا قالوا <span class='text-[#074182] dark:text-[#3D93F5]'>عنا؟</span>",
      },
      section_subtitle: {
        admin_title: "...",
        type: "textarea",
        value:
          "آراء طلابنا هي شهادة نجاحنا. انظر كيف ساعدناهم في تحقيق أهدافهم.",
      },
      reviews: {
        admin_title: "...",
        type: "repeater",
        value: [
          {
            name: "أحمد عبدالله",
            title: "طالب",
            quote: "منصة قادر ساعدتني كثيراً.",
          },
          {
            name: "فاطمة الزهراء",
            title: "طالبة",
            quote: "التنوع في الأسئلة كان ممتازاً.",
          },
          {
            name: "أحمد عبدالله",
            title: "طالب",
            quote: "منصة قادر ساعدتني كثيراً.",
          },
        ],
      },
    },
    images: [],
    icon_class: null,
    updated_at: new Date().toISOString(),
  },
  about_us: {
    slug: "homepage-about-us",
    title: "Homepage About Us Section",
    content: null,
    content_structured_resolved: {
      section_title: { admin_title: "...", type: "text", value: "من نحن؟" },
      section_text: {
        admin_title: "...",
        type: "textarea",
        value:
          "هنا يمكنك تقديم نفسك ومن أنت وما القصة التي تريد أن ترويها عن علامتك التجارية أو عملك.",
      },
      video_url: { admin_title: "...", type: "url", value: null },
      button_text: {
        admin_title: "...",
        type: "text",
        value: "تعرف علينا اكثر",
      },
      video_placeholder_image: {
        admin_title: "...",
        type: "image",
        value: "/images/video.png",
      },
    },
    images: [],
    icon_class: null,
    updated_at: new Date().toISOString(),
  },
  features: [
    {
      title: "الميزة الرئيسية 1",
      text: "وصف تفصيلي للميزة.",
      svg_image: null,
      icon_class: null,
    },
  ],
  statistics: [
    {
      label: "اختبار مكتمل",
      value: "+5000",
      icon_class: "fas fa-check-circle",
    },
  ],
  why_partner_text: {
    slug: "why-partner",
    title: "لماذا يجب على العملاء أن يختارونا؟",
    content: "نحن نقدم شريك نجاح متكامل.",
    content_structured_resolved: {
      section_title: {
        admin_title: "...",
        type: "text",
        value: "لماذا يجب على العملاء أن يختارونا؟",
      },
      section_subtitle: {
        admin_title: "...",
        type: "textarea",
        value: "ما الذي يجعلنا نتميز عن المنافسين.",
      },
      main_image: {
        admin_title: "...",
        type: "image",
        value: "/images/photo-1.png",
      },
    },
    images: [],
    icon_class: null,
    updated_at: new Date().toISOString(),
  },
  call_to_action: {
    slug: "homepage-cta",
    title: "Homepage Call To Action Section",
    content: null,
    content_structured_resolved: {
      title: {
        admin_title: "...",
        type: "text",
        value: "هل أنت مستعد للنجاح في اختبار القدرات؟",
      },
      subtitle: {
        admin_title: "...",
        type: "textarea",
        value:
          "انضم لآلاف الطلاب الذين حققوا أهدافهم مع منصة قادر. ابدأ رحلتك الآن!",
      },
      button_text: { admin_title: "...", type: "text", value: "اشتراك" },
    },
    images: [],
    icon_class: null,
    updated_at: new Date().toISOString(),
  },
};

/**
 * Fetches homepage content for Server-Side Rendering.
 * Preserves `null` for unpublished sections from the API.
 * Returns default data only if the entire API call fails.
 * @returns {Promise<HomepageData>} A promise that resolves to the final homepage data.
 */
export const getHomepageContent = async (): Promise<HomepageData> => {
  try {
    const apiData = await apiClient<HomepageData | null>("/content/homepage/", {
      isPublic: true,
    });

    if (!apiData) {
      return defaultHomepageData;
    }

    const processedData: HomepageData = {
      intro: apiData.intro
        ? { ...defaultHomepageData.intro, ...apiData.intro }
        : null,
      praise: apiData.praise
        ? { ...defaultHomepageData.praise, ...apiData.praise }
        : null,
      about_us: apiData.about_us
        ? { ...defaultHomepageData.about_us, ...apiData.about_us }
        : null,
      why_partner_text: apiData.why_partner_text
        ? {
            ...defaultHomepageData.why_partner_text,
            ...apiData.why_partner_text,
          }
        : null,
      call_to_action: apiData.call_to_action
        ? { ...defaultHomepageData.call_to_action, ...apiData.call_to_action }
        : null,
      features:
        apiData.features && apiData.features.length > 0
          ? apiData.features
          : null,
      statistics:
        apiData.statistics && apiData.statistics.length > 0
          ? apiData.statistics
          : null,
    };

    return processedData;
  } catch (error) {
    console.error(
      "Failed to fetch homepage content, using default data:",
      error
    );
    return defaultHomepageData;
  }
};

/**
 * Fetches content for the 'About Us' page.
 * @returns {Promise<Page<AboutPageContent> | null>} A promise resolving to the page data or null on error.
 */
export const getAboutPageContent =
  async (): Promise<Page<AboutPageContent> | null> => {
    try {
      // Use the generic Page API endpoint with the correct slug
      const pageData = await apiClient<Page<AboutPageContent>>(
        "/content/pages/our-story/",
        {
          isPublic: true,
        }
      );
      return pageData;
    } catch (error) {
      console.error("Failed to fetch About Us page content:", error);
      // Return null to indicate failure, the component will handle it
      return null;
    }
  };

/**
 * Fetches content for the 'Partners' page.
 * @returns {Promise<PartnersPageData | null>} A promise resolving to the page data or null on error.
 */
export const getPartnersPageContent =
  async (): Promise<PartnersPageData | null> => {
    try {
      const pageData = await apiClient<PartnersPageData>("/content/partners/", {
        isPublic: true,
      });
      return pageData;
    } catch (error) {
      console.error("Failed to fetch Partners page content:", error);
      return null;
    }
  };

/**
 * Fetches all content for the 'FAQ' page.
 * @returns {Promise<FaqPageData | null>} A promise resolving to the page data or null on error.
 */
export const getFaqPageContent = async (): Promise<FaqPageData | null> => {
  try {
    const pageData = await apiClient<FaqPageData>("/content/faq-page/", {
      isPublic: true,
    });
    return pageData;
  } catch (error) {
    console.error("Failed to fetch FAQ page content:", error);
    return null;
  }
};
