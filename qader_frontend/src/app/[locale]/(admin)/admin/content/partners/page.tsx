import { HydrationBoundary, dehydrate } from "@tanstack/react-query";
import getQueryClient from "@/lib/getQueryClient";
import { queryKeys } from "@/constants/queryKeys";
import { getPartnerCategories } from "@/services/api/admin/content.service";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { PATHS } from "@/constants/paths";
import { PartnerCategoriesClient } from "@/components/features/admin/content/partners/PartnerCategoriesClient";
import { getTranslations } from "next-intl/server";

export default async function AdminPartnerCategoriesPage() {
  const queryClient = getQueryClient();
  const t = await getTranslations("Admin.Content");

  await queryClient.prefetchQuery({
    queryKey: queryKeys.admin.content.partners.categories(),
    queryFn: getPartnerCategories,
  });

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <div className="space-y-2">
        <h1 className="text-2xl font-bold">{t("partners.pageTitle")}</h1>
        <p className="text-muted-foreground">{t("partners.pageDescription")}</p>
        <PartnerCategoriesClient />
      </div>
    </HydrationBoundary>
  );
}
