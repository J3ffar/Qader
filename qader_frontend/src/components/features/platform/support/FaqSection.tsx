// src/components/features/platform/support/FaqSection.tsx
"use client";

import { useMemo, useState } from "react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";
import type { FaqPageData } from "@/types/api/content.types";

interface FaqSectionProps {
  initialData: FaqPageData | null;
}

export default function FaqSection({ initialData }: FaqSectionProps) {
  const [searchTerm, setSearchTerm] = useState("");

  const heroTitle =
    initialData?.page_content?.content_structured_resolved?.hero_title.value ??
    "الأسئلة الشائعة";
  const heroSubtitle =
    initialData?.page_content?.content_structured_resolved?.hero_subtitle
      .value ?? "شاركنا استفسارك ليصلك الرد";

  const filteredFaqItems = useMemo(() => {
    if (!initialData?.faq_data) return [];

    const allItems = initialData.faq_data.flatMap((category) => category.items);

    if (!searchTerm.trim()) return allItems;

    const lowercasedFilter = searchTerm.toLowerCase();
    return allItems.filter(
      (item) =>
        item.question.toLowerCase().includes(lowercasedFilter) ||
        item.answer.toLowerCase().includes(lowercasedFilter)
    );
  }, [searchTerm, initialData]);

  return (
    <div className="text-center p-6 bg-card rounded-lg">
      <h1 className="text-3xl font-bold">{heroTitle}</h1>
      <p className="text-muted-foreground mt-2">{heroSubtitle}</p>
      <div className="relative max-w-lg mx-auto mt-6">
        <Search className="absolute rtl:right-3 ltr:left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
        <Input
          placeholder="اكتب سؤالك هنا..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full rtl:pr-10 ltr:pl-10"
        />
      </div>

      <Accordion
        type="single"
        collapsible
        className="w-full max-w-3xl mx-auto mt-6 text-right"
      >
        {filteredFaqItems.map((item) => (
          <AccordionItem value={`item-${item.id}`} key={item.id}>
            <AccordionTrigger className="font-semibold text-lg">
              {item.question}
            </AccordionTrigger>
            <AccordionContent className="text-muted-foreground">
              {item.answer}
            </AccordionContent>
          </AccordionItem>
        ))}
        {filteredFaqItems.length === 0 && (
          <p className="text-muted-foreground text-center py-4">
            {searchTerm
              ? `لا توجد نتائج لـ "${searchTerm}"`
              : "لا توجد أسئلة شائعة حاليًا."}
          </p>
        )}
      </Accordion>
    </div>
  );
}
