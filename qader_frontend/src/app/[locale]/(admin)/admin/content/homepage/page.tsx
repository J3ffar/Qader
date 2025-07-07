import { HydrationBoundary, dehydrate } from "@tanstack/react-query";
import getQueryClient from "@/lib/getQueryClient";
import { queryKeys } from "@/constants/queryKeys";
import {
  getHomepageFeatures,
  getHomepageStats,
} from "@/services/api/admin/content.service";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { PATHS } from "@/constants/paths";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { HomepageFeaturesClient } from "@/components/features/admin/content/homepage/HomepageFeaturesClient";
import { HomepageStatsClient } from "@/components/features/admin/content/homepage/HomepageStatsClient";

export default async function AdminHomepageContentPage() {
  const queryClient = getQueryClient();

  // Prefetch data for both tabs
  await Promise.all([
    queryClient.prefetchQuery({
      queryKey: queryKeys.admin.content.homepage.features(),
      queryFn: getHomepageFeatures,
    }),
    queryClient.prefetchQuery({
      queryKey: queryKeys.admin.content.homepage.stats(),
      queryFn: getHomepageStats,
    }),
  ]);

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
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
              <BreadcrumbPage>Homepage Management</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
        <h1 className="text-2xl font-bold">Manage Homepage Content</h1>
        <p className="text-muted-foreground">
          Control the dynamic cards and statistics displayed on the public
          homepage.
        </p>

        <Tabs defaultValue="features" className="w-full">
          <TabsList>
            <TabsTrigger value="features">Feature Cards</TabsTrigger>
            <TabsTrigger value="stats">Statistics</TabsTrigger>
          </TabsList>
          <TabsContent value="features">
            <HomepageFeaturesClient />
          </TabsContent>
          <TabsContent value="stats">
            <HomepageStatsClient />
          </TabsContent>
        </Tabs>
      </div>
    </HydrationBoundary>
  );
}
