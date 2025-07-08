import { HydrationBoundary, dehydrate } from "@tanstack/react-query";
import getQueryClient from "@/lib/getQueryClient";
import { queryKeys } from "@/constants/queryKeys";
import { getContactMessages } from "@/services/api/admin/content.service";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { PATHS } from "@/constants/paths";
import { ContactMessagesClient } from "@/components/features/admin/content/contact/ContactMessagesClient";
import { ITEMS_PER_PAGE } from "@/constants/config";
import Link from "next/link";
import { getTranslations } from "next-intl/server";

export default async function AdminContactMessagesPage() {
  const queryClient = getQueryClient();
  const t = await getTranslations("Admin.Content");
  const tContact = await getTranslations("Admin.Content.contact");

  const initialParams = {
    page: 1,
    page_size: ITEMS_PER_PAGE,
    ordering: "-created_at",
  };

  await queryClient.prefetchQuery({
    queryKey: queryKeys.admin.content.contact.list(initialParams),
    queryFn: () => getContactMessages(initialParams),
  });

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <div className="space-y-2">
        <h1 className="text-2xl font-bold">{tContact("pageTitle")}</h1>
        <p className="text-muted-foreground">{tContact("pageDescription")}</p>
        <ContactMessagesClient />
      </div>
    </HydrationBoundary>
  );
}
