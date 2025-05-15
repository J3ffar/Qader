"use client";

import React, { useEffect, useState } from "react";
import {
  ChevronDownIcon,
  MagnifyingGlassIcon,
  PaperAirplaneIcon,
} from "@heroicons/react/24/solid";

interface FaqItem {
  id: number;
  question: string;
  answer: string;
}

const fallbackData: Record<string, FaqItem[]> = {
  الطلاب: [
    { id: 1, question: "ما هو اختبار القدرات؟", answer: "هو اختبار لقياس القدرات التحليلية والمنطقية." },
    { id: 2, question: "كيف أستعد للاختبار؟", answer: "من خلال التدريب والمذاكرة عبر المنصة." },
    { id: 3, question: "هل يوجد دعم مباشر؟", answer: "نعم، تواصل معنا عبر صفحة الدعم." },
  ],
  الشراكة: [
    { id: 4, question: "ما هي أنواع الشراكات؟", answer: "محلية ودولية." },
    { id: 5, question: "كيف أصبح شريكًا؟", answer: "راسلنا عبر صفحة التواصل." },
  ],
  التحديات: [
    { id: 6, question: "هل هناك مسابقات؟", answer: "نعم، نعلن عنها بشكل دوري." },
    { id: 7, question: "كيف أشارك؟", answer: "عبر التسجيل في صفحة التحديات." },
  ],
};

const Questions: React.FC = () => {
  const [faqData, setFaqData] = useState<Record<string, FaqItem[]>>(fallbackData);
  const [activeSection, setActiveSection] = useState<string>("الطلاب");
  const [activeItem, setActiveItem] = useState<number | null>(null);

  useEffect(() => {
    const fetchFAQs = async () => {
      try {
        const res = await fetch("https://qader.vip/ar/api/v1/content/faq/");
        const apiData = await res.json();

        console.log("📦 FAQ Categories from API:", apiData);

        if (!Array.isArray(apiData.results)) return;

        const grouped: Record<string, FaqItem[]> = {};
        apiData.results.forEach((category: any) => {
          if (category.name && Array.isArray(category.items)) {
            grouped[category.name] = category.items;
          }
        });

        if (Object.keys(grouped).length > 0) {
          setFaqData(grouped);
          setActiveSection(grouped["الطلاب"] ? "الطلاب" : Object.keys(grouped)[0]);
        } else {
          throw new Error("No valid categories found");
        }
      } catch (err) {
        console.error("❌ Failed to fetch FAQ data. Using fallback.", err);
        setFaqData(fallbackData);
        setActiveSection("الطلاب");
      }
    };

    fetchFAQs();
  }, []);

  return (
    <div className="bg-white dark:bg-[#081028] sm:px-0 px-3">
      <div className="flex justify-center items-center gap-6 flex-col container mx-auto">
        <div className="text-center p-9">
          <h2 className="text-4xl font-bold">الأسئلة الشائعة</h2>
          <p className="text-gray-800 text-lg dark:text-[#D9E1FA]">
            لديك سؤال؟ لدينا الإجابة. ابحث عن سؤالك هنا أو تصفح التصنيفات.
          </p>
        </div>

        {/* Search Bar */}
        <div className="flex items-center gap-2 mt-6 p-9">
          <div className="relative w-full max-w-md shadow-md rounded-md border-[#D9E1FA] border-[1px]">
            <input
              type="text"
              placeholder="اكتب سؤالك هنا"
              className="w-full border-transparent hover:border-gray-300 rounded-lg py-2 pr-10 pl-4 focus:outline-none focus:ring-[#074182]"
            />
            <MagnifyingGlassIcon className="w-5 h-5 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2" />
          </div>

          <button className="bg-[#074182] text-white p-2 rounded-lg hover:bg-[#053866] transition">
            <MagnifyingGlassIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Categories Navbar */}
        <div className="p-10 w-full">
          <div className="flex gap-4 justify-center text-center border-b-1 flex-wrap">
            {Object.keys(faqData).map((section) => (
              <button
                key={section}
                onClick={() => {
                  setActiveSection(section);
                  setActiveItem(null);
                }}
                className={`py-2 px-4 font-semibold rounded-t-md transition-all border-b-2 ${
                  activeSection === section
                    ? "text-[#074182] border-[#074182]"
                    : "text-gray-700 border-transparent hover:text-[#074182]"
                }`}
              >
                {section}
              </button>
            ))}
          </div>

          {/* Questions List */}
          <ul className="mt-4 space-y-2 text-right">
            {faqData[activeSection]?.map((item) => (
              <li key={item.id}>
                <button
                  onClick={() =>
                    setActiveItem(item.id === activeItem ? null : item.id)
                  }
                  className="w-full flex items-center justify-between hover:text-[#074182] font-medium py-3 border-b-1 shadow-sm"
                >
                  <span className="font-bold">{item.question}</span>
                  <ChevronDownIcon
                    className={`w-4 h-4 text-gray-500 transition-transform duration-300 ${
                      activeItem === item.id ? "rotate-180" : ""
                    }`}
                  />
                </button>

                {activeItem === item.id && (
                  <div className="mt-1 bg-gray-50 dark:bg-transparent rounded p-2 transition">
                    <p>{item.answer}</p>
                  </div>
                )}
              </li>
            ))}
          </ul>
        </div>

        {/* Contact Prompt */}
        <div className="text-center flex flex-col justify-center items-center pb-9">
          <h2 className="text-4xl font-bold">هل ما زلت تحتاج مساعدة؟</h2>
          <a href="/contact">
            <button className="mt-4 flex justify-center gap-2 py-3 sm:w-[180px] w-[100px] p-2 rounded-[8px] bg-[#074182] text-[#FDFDFD] font-[600] hover:bg-[#074182DF] transition-all cursor-pointer">
              تواصل معنا <PaperAirplaneIcon className="text-white w-5 h-5" />
            </button>
          </a>
        </div>
      </div>
    </div>
  );
};

export default Questions;
