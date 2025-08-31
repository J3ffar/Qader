"use client";
import React, { useEffect, useRef } from "react";
import Image from "next/image";
import { ArrowUpLeft } from "lucide-react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import type { HomepageData } from "@/types/api/content.types";

// Register ScrollTrigger plugin
gsap.registerPlugin(ScrollTrigger);

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
  // Refs for animations
  const sectionRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const textRef = useRef<HTMLParagraphElement>(null);
  const buttonRef:any = useRef<HTMLAnchorElement>(null);
  const videoOverlayRef = useRef<HTMLDivElement>(null);

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

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Set initial states
      gsap.set([videoRef.current, titleRef.current, textRef.current, buttonRef.current], {
        opacity: 0,
      });

      // Create main timeline with updated ScrollTrigger settings
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: sectionRef.current,
          start: "top 120%", // CHANGED: Animation starts when section top is at 90% of viewport (much earlier)
          end: "center center", // CHANGED: Animation completes by the time section center reaches viewport center
          toggleActions: "play none none reverse",
          // markers: true, // Uncomment this to see visual markers for debugging
        }
      });

      // Video/Image animation - slide in from RIGHT with rotation (CHANGED: x: 100 instead of x: -100, rotateY: 30 instead of rotateY: -30)
      tl.fromTo(videoRef.current, 
        {
          opacity: 0,
          x: 100, // CHANGED: From right side (positive value)
          rotateY: 30, // CHANGED: Positive rotation
          scale: 0.8
        },
        {
          opacity: 1,
          x: 0,
          rotateY: 0,
          scale: 1,
          duration: 0.8, // CHANGED: Slightly faster duration
          ease: "power3.out",
        }
      );

      // Title animation - slide in from right with typewriter effect
      tl.fromTo(titleRef.current,
        {
          opacity: 0,
          x: 100, // CHANGED: Start from right
          y: 30,
          clipPath: "inset(0 0 0 100%)"
        },
        {
          opacity: 1,
          x: 0, // CHANGED: Move to center
          y: 0,
          clipPath: "inset(0 0 0 0%)",
          duration: 0.6, // CHANGED: Slightly faster duration
          ease: "power2.out"
        },
        "-=0.4" // CHANGED: More overlap with previous animation
      );

      // Text animation - slide in from right
      tl.fromTo(textRef.current,
        {
          opacity: 0,
          x: 80, // CHANGED: Start from right
          y: 20,
        },
        {
          opacity: 1,
          x: 0, // CHANGED: Move to center
          y: 0,
          duration: 0.5, // CHANGED: Slightly faster duration
          ease: "power2.out"
        },
        "-=0.3"
      );

      // Button animation - slide in from right with scale
      tl.fromTo(buttonRef.current,
        {
          opacity: 0,
          scale: 0.5,
          x: 60, // CHANGED: Start from right
          y: 20
        },
        {
          opacity: 1,
          scale: 1,
          x: 0, // CHANGED: Move to center
          y: 0,
          duration: 0.4, // CHANGED: Slightly faster duration
          ease: "back.out(1.7)"
        },
        "-=0.2"
      );

      // Add floating animation to the video/image container
      gsap.to(videoRef.current, {
        y: -10,
        duration: 2,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
        delay: 1
      });

      // Add glow effect on hover for video container
      if (videoRef.current) {
        videoRef.current.addEventListener("mouseenter", () => {
          gsap.to(videoRef.current, {
            scale: 1.02,
            duration: 0.3,
            ease: "power2.out",
            boxShadow: "0 20px 40px rgba(7, 65, 130, 0.3)"
          });
        });

        videoRef.current.addEventListener("mouseleave", () => {
          gsap.to(videoRef.current, {
            scale: 1,
            duration: 0.3,
            ease: "power2.out",
            boxShadow: "none"
          });
        });
      }

      // Parallax effect on scroll for the entire section
      gsap.to(sectionRef.current, {
        yPercent: -10,
        ease: "none",
        scrollTrigger: {
          trigger: sectionRef.current,
          start: "top bottom",
          end: "bottom top",
          scrub: 1
        }
      });

      // Add shimmer effect to title
      const shimmerAnimation = gsap.timeline({ repeat: -1, repeatDelay: 3 });
      shimmerAnimation.fromTo(titleRef.current,
        {
          backgroundImage: "linear-gradient(90deg, transparent 0%, rgba(231, 139, 72, 0.3) 50%, transparent 100%)",
          backgroundSize: "200% 100%",
          backgroundPosition: "-100% 0%",
          backgroundClip: "text",
          WebkitBackgroundClip: "text",
        },
        {
          backgroundPosition: "100% 0%",
          duration: 2,
          ease: "power2.inOut"
        }
      );

    }, sectionRef);

    // Button hover animations
    const handleButtonEnter = () => {
      gsap.to(buttonRef.current, {
        scale: 1.05,
        duration: 0.2,
        ease: "power2.out"
      });
      gsap.to(buttonRef.current?.querySelector('.arrow-icon'), {
        x: -3,
        y: -3,
        duration: 0.2,
        ease: "power2.out"
      });
    };

    const handleButtonLeave = () => {
      gsap.to(buttonRef.current, {
        scale: 1,
        duration: 0.2,
        ease: "power2.out"
      });
      gsap.to(buttonRef.current?.querySelector('.arrow-icon'), {
        x: 0,
        y: 0,
        duration: 0.2,
        ease: "power2.out"
      });
    };

    const buttonElement = buttonRef.current;
    if (buttonElement) {
      buttonElement.addEventListener("mouseenter", handleButtonEnter);
      buttonElement.addEventListener("mouseleave", handleButtonLeave);
    }

    // Cleanup
    return () => {
      ctx.revert();
      ScrollTrigger.getAll().forEach(trigger => trigger.kill());
      if (buttonElement) {
        buttonElement.removeEventListener("mouseenter", handleButtonEnter);
        buttonElement.removeEventListener("mouseleave", handleButtonLeave);
      }
    };
  }, []);

  return (
    <div ref={sectionRef} className="bg-white dark:bg-[#081028] sm:px-0 px-3 overflow-hidden transform-gpu">
      <div className="flex justify-center items-center py-6 gap-7 max-md:flex-col-reverse h-full container mx-auto px-0">
        {/* Video / Image Section */}
        <div 
          ref={videoRef}
          className="w-full max-w-[500px] h-[400px] aspect-video  rounded-lg overflow-hidden relative transform-gpu will-change-transform bg-transparent"
          style={{ perspective: "1000px" }}
        >
          {/* Animated overlay effect */}
          <div 
            ref={videoOverlayRef}
            className="absolute inset-0 bg-gradient-to-tr from-[#074182]/20 to-transparent opacity-0 hover:opacity-100 transition-opacity duration-300 pointer-events-none z-10"
          />
          
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
              width={300}
              height={500} 
              layout="responsive"
              priority
              className="w-full h-[500px] rounded-lg object-cover"
            />
          )}
        </div>

        {/* Text Content Section */}
        <div className="transform-gpu">
          <h2 
            ref={titleRef}
            className="text-4xl font-bold relative"
            style={{
              textShadow: "0 2px 10px rgba(0,0,0,0.1)"
            }}
          >
            {title}
          </h2>
          <p 
            ref={textRef}
            className="text-xl mt-4 text-gray-600 max-w-xl dark:text-[#D9E1FA] leading-relaxed"
          >
            {text}
          </p>
          <a 
            ref={buttonRef}
            href="/about"
            className="inline-block mt-4"
          >
            <button className="flex justify-center items-center gap-2 min-[1120px]:py-3 w-[220px] p-2 rounded-[8px] bg-[#074182] dark:bg-[#074182] text-[#FDFDFD] hover:bg-[#074182DF] dark:hover:bg-[#074182DF] transition-all cursor-pointer transform-gpu relative overflow-hidden group">
              <span className="relative z-10">{buttonText}</span>
              <ArrowUpLeft className="arrow-icon w-5 h-5 relative z-10 transform-gpu" />
              
              {/* Button ripple effect */}
              <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -skew-x-12 translate-x-[-200%] group-hover:translate-x-[200%] transition-transform duration-700 ease-out" />
            </button>
          </a>
        </div>
      </div>
    </div>
  );
};

export default AboutSection;
