import React from "react";
import Image from "next/image";
import Link from "next/link";
import { getFooterContent } from "@/services/content.service";
import type { SocialLinkFooter } from "@/types/api/content.types";

// Keep hardcoded nav links as requested
const footerNavLinks = [
  { name: "الرئيسية", ref: "/" },
  { name: "قصتنا", ref: "/about" },
  { name: "شركاء النجاح", ref: "/partners" },
  { name: "الأسئلة الشائعة", ref: "/questions" },
  { name: "تواصل معنا", ref: "/contact" },
];

const Footer = async () => {
  const data = await getFooterContent();
  const content = data?.content_structured_resolved;

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

  return (
    <footer className="w-full flex flex-col">
      {/* Main Footer Content */}
      <div className="bg-[#074182] dark:bg-[#081028] border-t border-gray-600 p-6 md:p-10 flex justify-center max-md:flex-col gap-10 text-white w-full">
        {/* Left Section (Logo, About, Social) */}
        <div className="flex-1">
          <div>
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
        <p>{finalCopyrightText}</p>
      </div>
    </footer>
  );
};

export default Footer;
