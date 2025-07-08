import { HydrationBoundary, dehydrate } from "@tanstack/react-query";
import { getPageBySlug } from "@/services/api/admin/content.service";
import { queryKeys } from "@/constants/queryKeys";
import getQueryClient from "@/lib/getQueryClient";
import { PageEditor } from "@/components/features/admin/content/pages/PageEditor";
import { notFound } from "next/navigation";
import { getTranslations } from "next-intl/server";

interface PageProps {
  params: Promise<{ local: string; slug: string }>;
}

export default async function AdminEditPage({ params }: PageProps) {
  const { slug } = await params;
  const queryClient = getQueryClient();
  const t = await getTranslations("Admin.Content");

  try {
    await queryClient.prefetchQuery({
      queryKey: queryKeys.admin.content.pages.detail(slug),
      queryFn: () => getPageBySlug(slug),
    });
  } catch (error) {
    notFound();
  }

  const page = queryClient.getQueryData<any>(
    queryKeys.admin.content.pages.detail(slug)
  );

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <PageEditor
        pageSlug={slug}
        pageTitle={page?.title ?? t("editPageTitle")}
      />
    </HydrationBoundary>
  );
}
