"use client";

import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useTranslations } from "next-intl";

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PATHS } from "@/constants/paths";
import { FaqCategoriesClient } from "@/components/features/admin/content/faqs/FaqCategoriesClient";
import { FaqItemsClient } from "@/components/features/admin/content/faqs/FaqItemsClient";
import type { FaqCategory } from "@/types/api/admin/content.types";

export default function AdminFaqsPage() {
  const [queryClient] = useState(() => new QueryClient());
  const [activeTab, setActiveTab] = useState("categories");
  const [selectedCategory, setSelectedCategory] = useState<FaqCategory | null>(
    null
  );

  const t = useTranslations("Admin.Content");
  const tFaqs = useTranslations("Admin.Content.faqs");

  const handleManageItems = (category: FaqCategory) => {
    setSelectedCategory(category);
    setActiveTab("items");
  };

  const handleBackToCategories = () => {
    setSelectedCategory(null);
    setActiveTab("categories");
  };

  return (
    <QueryClientProvider client={queryClient}>
      <div className="space-y-4">
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink href={PATHS.ADMIN.DASHBOARD}>
                {t("breadcrumbDashboard")}
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbLink href={PATHS.ADMIN.CONTENT_PAGES_LIST}>
                {t("breadcrumbContent")}
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbPage>{tFaqs("breadcrumb")}</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
        <h1 className="text-2xl font-bold">{tFaqs("pageTitle")}</h1>
        <p className="text-muted-foreground">{tFaqs("pageDescription")}</p>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList>
            <TabsTrigger value="categories" onClick={handleBackToCategories}>
              {tFaqs("tabs.categories")}
            </TabsTrigger>
            <TabsTrigger value="items" disabled={!selectedCategory}>
              {tFaqs("tabs.items", { name: selectedCategory?.name ?? "..." })}
            </TabsTrigger>
          </TabsList>
          <TabsContent value="categories">
            <FaqCategoriesClient onManageItems={handleManageItems} />
          </TabsContent>
          <TabsContent value="items">
            {selectedCategory && (
              <FaqItemsClient
                category={selectedCategory}
                onBack={handleBackToCategories}
              />
            )}
          </TabsContent>
        </Tabs>
      </div>
    </QueryClientProvider>
  );
}
