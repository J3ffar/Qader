"use client";
import React, { useState, useMemo } from "react";
import type { Page } from "@/types/api/content.types";

type TabKey = "terms" | "privacy";

interface ConditionsClientProps {
  initialData: {
    terms: Page<any> | null;
    privacy: Page<any> | null;
  };
}

// Helper function to generate a table of contents from the HTML content
const generateToc = (htmlContent: string) => {
  // Gracefully handle cases where there is no content or we are not in a browser environment.
  if (typeof window === "undefined" || !htmlContent) {
    return [];
  }

  // 1. Use the browser's built-in, reliable DOM parser.
  const parser = new DOMParser();
  const doc = parser.parseFromString(htmlContent, "text/html");

  // 2. Use a CSS selector to find all h3 elements that HAVE an id attribute.
  // This is not brittle and works regardless of quote style, attribute order, or inner HTML.
  const headings = doc.querySelectorAll("h3[id]");

  // 3. Extract the id and text content from each heading.
  return Array.from(headings).map((heading) => ({
    id: heading.id,
    title: heading.textContent || "", // Fallback to empty string if no text
  }));
};

const ConditionsClient: React.FC<ConditionsClientProps> = ({ initialData }) => {
  const [activeTab, setActiveTab] = useState<TabKey>("terms");

  const toc = useMemo(
    () => ({
      terms: generateToc(initialData.terms?.content || ""),
      privacy: generateToc(initialData.privacy?.content || ""),
    }),
    [initialData]
  );

  const scrollToId = (id: string) => {
    document
      .getElementById(id)
      ?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div className="flex flex-col md:flex-row p-4 md:p-10 gap-8 text-right dark:bg-[#081028]">
      {/* Sidebar */}
      <aside className="md:w-1/3 lg:w-1/4 sticky top-24 self-start">
        <div className="bg-white dark:bg-[#0B1739] p-4 rounded-xl shadow-lg">
          <div className="flex justify-around border-b border-gray-200 dark:border-gray-700 mb-4">
            <button
              onClick={() => setActiveTab("terms")}
              className={`text-lg font-bold pb-2 px-2 transition-colors duration-200 ${
                activeTab === "terms"
                  ? "text-[#074182] dark:text-[#3D93F5] border-b-2 border-[#074182] dark:border-[#3D93F5]"
                  : "text-gray-600 dark:text-gray-300 hover:text-black dark:hover:text-white"
              }`}
            >
              الشروط والأحكام
            </button>
            <button
              onClick={() => setActiveTab("privacy")}
              className={`text-lg font-bold pb-2 px-2 transition-colors duration-200 ${
                activeTab === "privacy"
                  ? "text-[#074182] dark:text-[#3D93F5] border-b-2 border-[#074182] dark:border-[#3D93F5]"
                  : "text-gray-600 dark:text-gray-300 hover:text-black dark:hover:text-white"
              }`}
            >
              سياسة الخصوصية
            </button>
          </div>
          <p className="text-lg font-bold text-gray-800 dark:text-gray-100 mb-4 text-center">
            جدول المحتويات
          </p>
          <ul className="space-y-3 text-gray-700 dark:text-gray-300">
            {toc[activeTab].map((item) => (
              <li key={item.id}>
                <button
                  onClick={() => scrollToId(item.id)}
                  className="text-right w-full hover:text-[#2F80ED] transition-colors"
                >
                  {item.title}
                </button>
              </li>
            ))}
          </ul>
        </div>
      </aside>

      {/* Content */}
      <main className="md:w-2/3 lg:w-3/4 bg-white dark:bg-[#0B1739] p-6 md:p-8 rounded-xl shadow-lg">
        <article
          // --- START OF CHANGE ---
          // The className is now much simpler.
          className="prose-lg dark:prose-invert max-w-none"
          // --- END OF CHANGE ---
          dangerouslySetInnerHTML={{
            __html:
              initialData[activeTab]?.content ||
              `<p>لا يتوفر محتوى حالياً.</p>`,
          }}
        />
      </main>
    </div>
  );
};

export default ConditionsClient;
