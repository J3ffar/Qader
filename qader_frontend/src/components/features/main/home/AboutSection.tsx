import React from "react";
import Image from "next/image";
import { ArrowUpLeft } from "lucide-react";
import type { HomepageData } from "@/types/api/content.types";

type AboutSectionProps = {
  data: HomepageData["about_us"];
};

/**
 * Transforms a standard YouTube URL into an embeddable URL.
 * @param url The original YouTube URL.
 * @returns The embeddable URL, or null if the original URL is invalid.
 */
const getYouTubeEmbedUrl = (url: string | null | undefined): string | null => {
  if (!url) {
    return null;
  }
  try {
    const urlObj = new URL(url);
    // Standard link: https://www.youtube.com/watch?v=VIDEO_ID
    if (
      urlObj.hostname === "www.youtube.com" ||
      urlObj.hostname === "youtube.com"
    ) {
      const videoId = urlObj.searchParams.get("v");
      if (videoId) {
        return `https://www.youtube.com/embed/${videoId}`;
      }
    }
    // Shortened link: https://youtu.be/VIDEO_ID
    if (urlObj.hostname === "youtu.be") {
      const videoId = urlObj.pathname.slice(1); // Remove the leading '/'
      if (videoId) {
        return `https://www.youtube.com/embed/${videoId}`;
      }
    }
  } catch (error) {
    console.error("Invalid URL for YouTube embed:", url, error);
    return null;
  }
  return null; // Return null if it's not a recognizable YouTube URL
};

const AboutSection = ({ data }: AboutSectionProps) => {
  const title =
    data?.content_structured_resolved?.section_title?.value ?? "من نحن؟";
  const text =
    data?.content_structured_resolved?.section_text?.value ??
    "هنا يمكنك تقديم نفسك ومن أنت وما القصة التي تريد أن ترويها عن علامتك التجارية أو عملك.";
  const originalVideoUrl = data?.content_structured_resolved?.video_url?.value;
  const buttonText =
    data?.content_structured_resolved?.button_text?.value ?? "تعرف علينا اكثر";
  const placeholderImage =
    data?.content_structured_resolved?.video_placeholder_image?.value ??
    "/images/video.png";

  // Use the helper function to get the correct embed URL
  // const embedUrl = getYouTubeEmbedUrl(originalVideoUrl);
  const embedUrl = originalVideoUrl;

  return (
    <div className=" bg-white dark:bg-[#081028] sm:px-0 px-3">
      <div className="flex justify-center items-center py-6 gap-7 max-md:flex-col-reverse h-full container mx-auto px-0 ">
        {/* Video / Image Section */}
        <div className="w-full max-w-[600px] aspect-video h-auto rounded-lg overflow-hidden bg-gray-200">
          {embedUrl ? (
            <iframe
              width="100%"
              height="100%"
              src={embedUrl}
              title="YouTube video player"
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
              referrerPolicy="strict-origin-when-cross-origin"
              allowFullScreen
              className="w-full h-full"
            ></iframe>
          ) : (
            <Image
              src={placeholderImage}
              alt="عرض تقديمي عن منصة قادر"
              width={600}
              height={338} // Adjusted for 16:9 aspect ratio
              layout="responsive"
              priority
              className="w-full h-auto rounded-lg object-cover"
            />
          )}
        </div>

        {/* Text Content Section */}
        <div>
          <h2 className="text-4xl font-bold">{title}</h2>
          <p className="text-xl mt-4 text-gray-600 max-w-xl dark:text-[#D9E1FA]">
            {text}
          </p>
          <a href="/about">
            <button className=" mt-4 flex justify-center items-center gap-2 min-[1120px]:py-3 w-[220px] p-2 rounded-[8px] bg-[#074182] dark:bg-[#074182] text-[#FDFDFD]  hover:bg-[#074182DF] dark:hover:bg-[#074182DF] transition-all cursor-pointer">
              <span>{buttonText}</span>
              <ArrowUpLeft className="w-5 h-5" />
            </button>
          </a>
        </div>
      </div>
    </div>
  );
};

export default AboutSection;
