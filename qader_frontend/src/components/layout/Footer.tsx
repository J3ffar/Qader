"use client";

import React, { useEffect, useRef, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { gsap } from "gsap";
import type { SocialLinkFooter } from "@/types/api/content.types";

// Keep hardcoded nav links as requested
const footerNavLinks = [
  { name: "الرئيسية", ref: "/" },
  { name: "قصتنا", ref: "/about" },
  { name: "شركاء النجاح", ref: "/partners" },
  { name: "الأسئلة الشائعة", ref: "/questions" },
  { name: "تواصل معنا", ref: "/contact" },
];

// Define interfaces for the content structure
interface FooterContent {
  about_title?: { value: string };
  about_text?: { value: string };
  follow_us_title?: { value: string };
  social_links?: { value: SocialLinkFooter[] };
  copyright_text?: { value: string };
}

interface FooterData {
  content_structured_resolved?: FooterContent;
}

const Footer: React.FC = () => {
  const logoRef = useRef<HTMLDivElement>(null);
  const socialIconsRef = useRef<(HTMLAnchorElement | null)[]>([]);
  const copyrightRef = useRef<HTMLParagraphElement>(null);
  
  // State for dynamic content
  const [footerData, setFooterData] = useState<FooterData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch footer content on client side
  useEffect(() => {
    const fetchFooterContent = async () => {
      try {
        // Import the service dynamically on client side
        const { getFooterContent } = await import("@/services/content.service");
        const data = await getFooterContent();
        setFooterData(data);
      } catch (error) {
        console.error("Failed to fetch footer content:", error);
        // Set empty data to use defaults
        setFooterData(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchFooterContent();
  }, []);

  const content = footerData?.content_structured_resolved;

  // Define default values for all editable content
  const aboutTitle = content?.about_title?.value ?? "نبذة بسيطة عن قادر";
  const aboutText =
    content?.about_text?.value ??
    "منصة تعليمية رائدة لتمكين الطلاب في اختبارات القدرات.";
  const followUsTitle = content?.follow_us_title?.value ?? "تابع منصتنا";
  const socialLinks: SocialLinkFooter[] = content?.social_links?.value ?? [];
  const copyrightText =
    content?.copyright_text?.value ?? "© جميع الحقوق محفوظة {YEAR}";

  // Replace {YEAR} placeholder with the current year
  const finalCopyrightText = copyrightText.replace(
    "{YEAR}",
    new Date().getFullYear().toString()
  );

  useEffect(() => {
    if (isLoading) return; // Don't run animations until content is loaded

    // Logo infinite subtle animation (gentle floating effect)
    if (logoRef.current) {
      gsap.to(logoRef.current, {
        y: -8,
        duration: 2,
        ease: "power2.inOut",
        yoyo: true,
        repeat: -1,
      });
      
      // Add a subtle rotation animation
      gsap.to(logoRef.current, {
        rotation: 3,
        duration: 3,
        ease: "power2.inOut",
        yoyo: true,
        repeat: -1,
      });
    }

    // Social media icons hover animations
    const cleanupFunctions: (() => void)[] = [];
    
    socialIconsRef.current.forEach((icon) => {
      if (icon) {
        const handleMouseEnter = () => {
          gsap.to(icon, {
            rotation: 360,
            scale: 1.1,
            duration: 0.6,
            ease: "power2.out",
          });
        };

        const handleMouseLeave = () => {
          gsap.to(icon, {
            rotation: 0,
            scale: 1,
            duration: 0.4,
            ease: "power2.out",
          });
        };

        icon.addEventListener("mouseenter", handleMouseEnter);
        icon.addEventListener("mouseleave", handleMouseLeave);

        // Store cleanup function
        cleanupFunctions.push(() => {
          icon.removeEventListener("mouseenter", handleMouseEnter);
          icon.removeEventListener("mouseleave", handleMouseLeave);
        });
      }
    });

    // Typewriter effect for copyright text
    if (copyrightRef.current) {
      const text = finalCopyrightText;
      copyrightRef.current.textContent = "";
      
      // Create a timeline for the typewriter effect
      const tl = gsap.timeline({ delay: 1 });
      
      // Split text into characters and animate each one
      for (let i = 0; i < text.length; i++) {
        tl.to(copyrightRef.current, {
          duration: 0.05,
          ease: "none",
          onUpdate: function() {
            if (copyrightRef.current) {
              copyrightRef.current.textContent = text.substring(0, i + 1);
            }
          }
        });
      }
      
      // Add blinking cursor effect
      gsap.to(copyrightRef.current, {
        opacity: 0.3,
        duration: 0.8,
        ease: "power2.inOut",
        yoyo: true,
        repeat: -1,
        delay: text.length * 0.05 + 1.5,
      });
      
      // Add subtle text shadow animation after typing is complete
      gsap.to(copyrightRef.current, {
        textShadow: "0 0 10px rgba(255, 255, 255, 0.3)",
        duration: 1.5,
        ease: "power2.inOut",
        yoyo: true,
        repeat: -1,
        delay: text.length * 0.05 + 2,
      });
    }

    // Cleanup function for social icons
    return () => {
      cleanupFunctions.forEach(cleanup => cleanup());
    };
  }, [finalCopyrightText, isLoading]);

  // Show loading state or render with defaults
  if (isLoading) {
    return (
      <footer className="w-full flex flex-col">
        {/* Loading skeleton */}
        <div className="bg-[#074182] dark:bg-[#081028] border-t border-gray-600 p-6 md:p-10 flex justify-center max-md:flex-col gap-10 text-white w-full">
          <div className="flex-1">
            <div className="animate-pulse">
              <div className="w-24 h-24 bg-gray-300 rounded"></div>
              <div className="h-8 bg-gray-300 rounded mt-8 w-48"></div>
              <div className="h-4 bg-gray-300 rounded mt-2 w-full max-w-md"></div>
              <div className="flex gap-4 mt-8">
                <div className="h-6 bg-gray-300 rounded w-24"></div>
                <div className="w-10 h-10 bg-gray-300 rounded-full"></div>
                <div className="w-10 h-10 bg-gray-300 rounded-full"></div>
              </div>
            </div>
          </div>
          <div className="flex-1 flex justify-center gap-10 max-md:justify-start max-md:mt-6">
            <div className="animate-pulse">
              <div className="h-6 bg-gray-300 rounded w-20"></div>
              <div className="space-y-2 mt-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="h-4 bg-gray-300 rounded w-24"></div>
                ))}
              </div>
            </div>
            <div className="animate-pulse">
              <div className="h-6 bg-gray-300 rounded w-20"></div>
              <div className="space-y-2 mt-4">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="h-4 bg-gray-300 rounded w-28"></div>
                ))}
              </div>
            </div>
          </div>
        </div>
        <div className="bg-[#053061] dark:bg-[#031830] text-white font-medium text-center py-3 w-full">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-300 rounded w-48 mx-auto"></div>
          </div>
        </div>
      </footer>
    );
  }

  return (
    <footer className="w-full flex flex-col">
      {/* Main Footer Content */}
      <div className="bg-[#074182] dark:bg-[#081028] border-t border-gray-600 p-6 md:p-10 flex justify-center max-md:flex-col gap-10 text-white w-full">
        {/* Left Section (Logo, About, Social) */}
        <div className="flex-1">
          <div ref={logoRef} className="inline-block">
            <Image
              alt="Qader Logo"
              src="/images/logo.png" // This image remains hardcoded as requested
              width={100}
              height={100}
            />
          </div>
          <h3 className="font-bold text-2xl mt-8">{aboutTitle}</h3>
          <p className="mt-2 text-gray-300 leading-relaxed">{aboutText}</p>

          <div className="flex gap-4 mt-8 items-center flex-wrap">
            <h3 className="font-bold text-xl">{followUsTitle}</h3>
             {socialLinks.map((social, index) => (
              <a
                key={index}
                href={social.url}
                ref={(el:any) => (socialIconsRef.current[index] = el)}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={`تابعنا على ${social.icon_slug}`}
              >
                <span className="flex items-center justify-center w-10 h-10 p-2 rounded-full bg-gray-200 dark:bg-gray-700 transition hover:bg-gray-300 dark:hover:bg-gray-600">
                  <Image
                    src={"/images/" + social.icon_slug + ".png"} // Uses dynamic URL with fallback
                    alt={`ايقونة ${social.icon_slug}`}
                    width={24}
                    height={24}
                  />
                </span>
              </a>
            ))}
          </div>
        </div>

        {/* Right Section (Links) */}
        <div className="flex-1 flex justify-center gap-10 max-md:justify-start max-md:mt-6">
          {/* Pages Links */}
          <div>
            <h3 className="font-bold text-xl">الصفحات</h3>
            <ul className="flex flex-col mt-4 space-y-2">
              {footerNavLinks.map((item) => (
                <li key={item.name}>
                  <Link
                    href={item.ref}
                    className="text-gray-300 transition-colors duration-300 hover:text-white"
                  >
                    {item.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
          {/* Terms & Contact Links */}
          <div className="flex flex-col">
            <h3 className="font-bold text-xl">روابط مهمة</h3>
            <ul className="flex flex-col mt-4 space-y-2">
              <li>
                <Link
                  href="/terms-and-conditions"
                  className="text-gray-300 hover:text-white"
                >
                  الشروط والأحكام
                </Link>
              </li>
              <li>
                <Link
                  href="/privacy"
                  className="text-gray-300 hover:text-white"
                >
                  سياسة الخصوصية
                </Link>
              </li>
              <li>
                <Link
                  href="/contact"
                  className="text-gray-300 hover:text-white"
                >
                  تواصل معنا
                </Link>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Copyright Bar */}
      <div className="bg-[#053061] dark:bg-[#031830] text-white font-medium text-center py-3 w-full">
        <p ref={copyrightRef} className="relative">
          {/* Text will be populated by GSAP animation */}
        </p>
      </div>
    </footer>
  );
};

export default Footer;
