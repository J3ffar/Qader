"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { Page } from "@/types/api/content.types";

const PrivacyClient = ({ content }: { content: Page<any> | null }) => {
  const [toc, setToc] = useState<{ id: string; title: string }[]>([]);

  useEffect(() => {
    if (!content?.content) return;

    const parser = new DOMParser();
    const doc = parser.parseFromString(content.content, "text/html");
    const headings = doc.querySelectorAll("h3[id]");
    const items = Array.from(headings).map((h) => ({
      id: h.id,
      title: h.textContent || "",
    }));
    setToc(items);
  }, [content]);

  const scrollToId = (id: string) => {
    document
      .getElementById(id)
      ?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div className="flex flex-col md:flex-row p-4 md:p-10 gap-8 text-right dark:bg-[#081028]">
      <aside className="md:w-1/3 lg:w-1/4 sticky top-24 self-start">
        <div className="bg-white dark:bg-[#0B1739] p-4 rounded-xl shadow-lg">
          <div className="flex justify-around border-b border-gray-200 dark:border-gray-700 mb-4">
            <Link
              href="/terms-and-conditions"
              className="text-lg font-bold pb-2 px-2 text-gray-600 dark:text-gray-300 hover:text-black dark:hover:text-white"
            >
              الشروط والأحكام
            </Link>
            <Link
              href="#"
              className="text-lg font-bold pb-2 px-2 text-[#074182] dark:text-[#3D93F5] border-b-2 border-[#074182] dark:border-[#3D93F5]"
            >
              سياسة الخصوصية
            </Link>
          </div>
          <p className="text-lg font-bold text-gray-800 dark:text-gray-100 mb-4 text-center">
            جدول المحتويات
          </p>
          <ul className="space-y-3 text-gray-700 dark:text-gray-300">
            {toc.map((item) => (
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

      <main className="md:w-2/3 lg:w-3/4 bg-white dark:bg-[#0B1739] p-6 md:p-8 rounded-xl shadow-lg">
        <article
          className="prose-lg dark:prose-invert max-w-none"
          dangerouslySetInnerHTML={{
            __html: content?.content || "<p>لا يتوفر محتوى حالياً.</p>",
          }}
        />
      </main>
    </div>
  );
};

export default PrivacyClient;
