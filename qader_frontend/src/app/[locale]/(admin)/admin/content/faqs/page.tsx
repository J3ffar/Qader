"use client"; // This page needs to manage state, so it must be a client component.

import { useState } from "react";
import {
  HydrationBoundary,
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";
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
      <HydrationBoundary>
        <div className="space-y-4">
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbLink href={PATHS.ADMIN.DASHBOARD}>
                  Dashboard
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbLink href={PATHS.ADMIN.CONTENT_PAGES_LIST}>
                  Content
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbPage>FAQ Management</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
          <h1 className="text-2xl font-bold">Manage FAQs</h1>
          <p className="text-muted-foreground">
            Organize questions and answers into categories for the public FAQ
            page.
          </p>

          <Tabs
            value={activeTab}
            onValueChange={setActiveTab}
            className="w-full"
          >
            <TabsList>
              <TabsTrigger value="categories" onClick={handleBackToCategories}>
                Categories
              </TabsTrigger>
              <TabsTrigger value="items" disabled={!selectedCategory}>
                Items in "{selectedCategory?.name ?? "..."}"
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
      </HydrationBoundary>
    </QueryClientProvider>
  );
}
