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

export default async function AdminContactMessagesPage() {
  const queryClient = getQueryClient();
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
              <BreadcrumbPage>Contact Messages</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
        <h1 className="text-2xl font-bold">Contact Message Inbox</h1>
        <p className="text-muted-foreground">
          View and manage messages submitted through the public contact form.
        </p>
        <ContactMessagesClient />
      </div>
    </HydrationBoundary>
  );
}
