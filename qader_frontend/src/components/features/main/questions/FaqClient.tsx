"use client";

import React, { useState, useMemo } from "react";
import {
  ChevronDownIcon,
  MagnifyingGlassIcon,
  PaperAirplaneIcon,
} from "@heroicons/react/24/solid";
import type { FaqPageData } from "@/types/api/content.types";
import Link from "next/link";

interface FaqClientProps {
  data: FaqPageData | null;
}

const FaqClient: React.FC<FaqClientProps> = ({ data }) => {
  const [activeCategoryName, setActiveCategoryName] = useState<string>(
    data?.faq_data?.[0]?.name ?? ""
  );
  const [activeItem, setActiveItem] = useState<number | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  const pageContent = data?.page_content?.content_structured_resolved;
  const heroTitle = pageContent?.hero_title.value ?? "الأسئلة الشائعة";
  const heroSubtitle =
    pageContent?.hero_subtitle.value ?? "لديك سؤال؟ لدينا الإجابة.";
  const ctaTitle = pageContent?.cta_title.value ?? "هل ما زلت تحتاج مساعدة؟";
  const ctaButtonText = pageContent?.cta_button_text.value ?? "تواصل معنا";

  // Memoize the filtered data to avoid re-calculating on every render
  const filteredFaqData = useMemo(() => {
    if (!data?.faq_data) return [];
    if (!searchTerm.trim()) return data.faq_data;

    const lowercasedFilter = searchTerm.toLowerCase();

    return data.faq_data
      .map((category) => ({
        ...category,
        items: category.items.filter(
          (item) =>
            item.question.toLowerCase().includes(lowercasedFilter) ||
            item.answer.toLowerCase().includes(lowercasedFilter)
        ),
      }))
      .filter((category) => category.items.length > 0);
  }, [searchTerm, data]);

  // Effect to reset active category if it's no longer in the filtered list
  React.useEffect(() => {
    if (
      filteredFaqData.length > 0 &&
      !filteredFaqData.some((c) => c.name === activeCategoryName)
    ) {
      setActiveCategoryName(filteredFaqData[0].name);
    } else if (filteredFaqData.length === 0) {
      setActiveCategoryName("");
    }
  }, [filteredFaqData, activeCategoryName]);

  return (
    <div className="bg-white dark:bg-[#081028] sm:px-0 px-3 py-10">
      <div className="flex justify-center items-center gap-6 flex-col container mx-auto">
        <div className="text-center px-4">
          <h2 className="text-4xl font-bold">{heroTitle}</h2>
          <p className="text-gray-800 text-lg dark:text-[#D9E1FA] mt-2">
            {heroSubtitle}
          </p>
        </div>

        {/* Search Bar */}
        <div className="relative w-full max-w-lg shadow-md rounded-lg">
          <input
            type="text"
            placeholder="اكتب كلمة للبحث في الأسئلة والأجوبة..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full border-gray-300 dark:border-gray-600 dark:bg-gray-800 rounded-lg py-3 pr-10 pl-4 focus:outline-none focus:ring-2 focus:ring-[#074182]"
          />
          <MagnifyingGlassIcon className="w-5 h-5 text-gray-400 absolute right-4 top-1/2 -translate-y-1/2" />
        </div>

        {/* Categories Navbar */}
        <div className="p-4 md:p-10 w-full">
          <div className="flex gap-4 justify-center text-center border-b border-gray-200 dark:border-gray-700 flex-wrap">
            {filteredFaqData.map((category) => (
              <button
                key={category.id}
                onClick={() => {
                  setActiveCategoryName(category.name);
                  setActiveItem(null);
                }}
                className={`py-2 px-4 font-semibold rounded-t-md transition-all border-b-2 ${
                  activeCategoryName === category.name
                    ? "text-[#074182] border-[#074182]"
                    : "text-gray-600 dark:text-gray-300 border-transparent hover:text-[#074182] hover:border-gray-300"
                }`}
              >
                {category.name}
              </button>
            ))}
          </div>

          {/* Questions List */}
          <div className="mt-4 space-y-2">
            {filteredFaqData
              .find((c) => c.name === activeCategoryName)
              ?.items.map((item) => (
                <div
                  key={item.id}
                  className="border-b border-gray-200 dark:border-gray-700"
                >
                  <button
                    onClick={() =>
                      setActiveItem(item.id === activeItem ? null : item.id)
                    }
                    className="w-full flex items-center justify-between text-right font-medium py-4"
                  >
                    <span className="font-bold text-lg">{item.question}</span>
                    <ChevronDownIcon
                      className={`w-5 h-5 text-gray-500 transition-transform duration-300 ${
                        activeItem === item.id ? "rotate-180" : ""
                      }`}
                    />
                  </button>
                  {activeItem === item.id && (
                    <div className="pb-4 pr-2 text-gray-700 dark:text-gray-300 leading-relaxed">
                      <p>{item.answer}</p>
                    </div>
                  )}
                </div>
              ))}
            {filteredFaqData.length > 0 &&
              !filteredFaqData.find((c) => c.name === activeCategoryName) && (
                <p className="text-center text-gray-500 py-10">
                  الرجاء اختيار تصنيف لعرض الأسئلة.
                </p>
              )}
            {filteredFaqData.length === 0 && searchTerm && (
              <p className="text-center text-gray-500 py-10">
                لا توجد نتائج بحث تطابق '{searchTerm}'
              </p>
            )}
          </div>
        </div>

        {/* Contact Prompt */}
        <div className="text-center flex flex-col justify-center items-center pb-9">
          <h2 className="text-4xl font-bold">{ctaTitle}</h2>
          <Link href="/contact" passHref>
            <button className="mt-4 flex items-center justify-center gap-2 py-3 px-8 rounded-lg bg-[#074182] text-white font-semibold hover:bg-[#053061] transition-all">
              {ctaButtonText} <PaperAirplaneIcon className="w-5 h-5" />
            </button>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default FaqClient;
