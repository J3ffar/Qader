import { HydrationBoundary, dehydrate } from "@tanstack/react-query";
import { getPages } from "@/services/api/admin/content.service";
import { queryKeys } from "@/constants/queryKeys";
import getQueryClient from "@/lib/getQueryClient";
import { PagesClient } from "@/components/features/admin/content/pages/PagesClient";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { PATHS } from "@/constants/paths";

export default async function AdminPagesManagementPage() {
  const queryClient = getQueryClient();
  const params = { ordering: "id" };

  await queryClient.prefetchQuery({
    // Use the new parameterized query key
    queryKey: queryKeys.admin.content.pages.list(params),
    // Pass the ordering parameter to the fetch function
    queryFn: () => getPages(params),
  });

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
              <BreadcrumbPage>Content Management</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
        <h1 className="text-2xl font-bold">Manage Pages</h1>
        <p className="text-muted-foreground">
          Edit content for static and structured pages across the platform.
        </p>
        <PagesClient />
      </div>
    </HydrationBoundary>
  );
}
