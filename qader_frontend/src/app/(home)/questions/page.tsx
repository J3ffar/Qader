"use client";

import React, { useState } from "react";
import { ChevronDownIcon, MagnifyingGlassIcon } from "@heroicons/react/24/solid";

const data = {
  الطلاب: ["السؤال1", "السؤال2", "السؤال3"],
  الشراكة: ["شريك محلي", "شريك دولي"],
  التحديات: ["تحدي 1", "تحدي 2"],
};

const Questions: React.FC = () => {
  const [activeSection, setActiveSection] = useState<string | null>("الطلاب");
  const [activeItem, setActiveItem] = useState<string | null>(null);

    return (
        <div className="flex justify-center items-center gap-6 flex-col container mx-auto">
            <div className="text-center p-9">
                <h2 className="text-4xl font-bold">الأسئلةالشائعة</h2>
                <p className="text-gray-800 text-lg dark:text-[#D9E1FA]">لديك سؤال؟ لديناالاجابة, ابحث عن سؤالك هنا.ديك سؤال؟ لديناالاجابة, ابحث عن سؤالك هنا.
                    ديك سؤال؟ لديناالاجابة, ابحث عن سؤالك هنا.
                ديك سؤال؟ لديناالاجابة, ابحث عن سؤالك هنا.</p>
            </div>
            <div className="flex items-center gap-2 mt-6 p-9">
  {/* Input wrapper */}
  <div className="relative w-full max-w-md shadow-md rounded-md border-[#D9E1FA] border-[1px]">
    <input
      type="text"
      placeholder="اكتب سؤالك هنا"
      className="w-full border-transparent hover:border-gray-300 rounded-lg py-2 pr-10 pl-4 focus:outline-none focus:ring-[#074182]"
    />
  
    <MagnifyingGlassIcon className="w-5 h-5 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2 " />
  </div>

 
  <button className="bg-[#074182] text-white p-2 rounded-lg hover:bg-[#053866] transition dark:border-[#3D93F5] dark:bg-[#3D93F5]">
    <MagnifyingGlassIcon className="w-5 h-5" />
  </button>
           </div>
           <div className="p-20 w-full">
      {/* Navbar */}
      <div className="flex gap-4 justify-center text-center border-b-1">
        {Object.keys(data).map((section) => (
          <button
            key={section}
            onClick={() => {
              if (section !== activeSection) {
                setActiveSection(section);
                setActiveItem(null);
              }
            }}
            className={`py-2 px-4 font-semibold rounded-t-md transition-all border-b-1 ${
              activeSection === section
                ? "text-[#074182] border-[#074182] dark:text-[#3D93F5] dark:border-[#3D93F5]"
                : "text-gray-700 dark:text-[#D9E1FA] hover:text-[#074182] border-transparent"
            }`}
          >
            {section}
          </button>
        ))}
      </div>

      {/* التصنيفات الفرعية */}
      {activeSection && (
        <ul className="mt-4 space-y-2 text-right">
          {data[activeSection as keyof typeof data].map((item) => (
            <li key={item}>
              <button
                onClick={() =>
                  setActiveItem(item === activeItem ? null : item)
                }
                className="w-full flex items-center justify-between hover:text-[#074182] font-medium py-3 border-b-1 shadow-2xs"
              >
                <span className="font-bold">{item}</span>
                <ChevronDownIcon
                  className={`w-4 h-4 text-gray-500 transition-transform duration-300 ${
                    activeItem === item ? "rotate-180" : ""
                  }`}
                />
              </button>

              {activeItem === item && (
                <div className="mt-1 bg-gray-50 dark:bg-[#074182] rounded p-2 transition delay-150 duration-300 ease-in-out">
                      <p className="font-bold">كيف يتم الأشتراك فى المنصة</p>
                      <p>شرح كيفية الأشتراك مع وجود روابط سريعة الانتقال</p>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
            </div>
      </div>
  );
};

export default Questions;
