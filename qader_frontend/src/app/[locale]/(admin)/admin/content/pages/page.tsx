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
import { getTranslations } from "next-intl/server";

export default async function AdminPagesManagementPage() {
  const queryClient = getQueryClient();
  const params = { ordering: "id" };
  const t = await getTranslations("Admin.Content");

  await queryClient.prefetchQuery({
    queryKey: queryKeys.admin.content.pages.list(params),
    queryFn: () => getPages(params),
  });

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
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
              <BreadcrumbPage>{t("breadcrumbContent")}</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
        <h1 className="text-2xl font-bold">{t("pagesListTitle")}</h1>
        <p className="text-muted-foreground">{t("pagesListDescription")}</p>
        <PagesClient />
      </div>
    </HydrationBoundary>
  );
}
