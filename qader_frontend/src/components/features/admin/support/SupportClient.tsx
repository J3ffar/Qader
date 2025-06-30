"use client";

import { useMemo } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { getSupportTickets } from "@/services/api/admin/support.service";
import { queryKeys } from "@/constants/queryKeys";
import { SupportTableSkeleton } from "./SupportTableSkeleton";
import { SupportTable } from "./SupportTable";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Terminal } from "lucide-react";
import { ITEMS_PER_PAGE } from "@/constants/config";

export function SupportClient() {
  const t = useTranslations("Errors");
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // useMemo ensures this object is stable unless searchParams change
  const queryParams = useMemo(() => {
    const params = new URLSearchParams(searchParams);
    return {
      page: params.get("page") || "1",
      search: params.get("search") || "",
      status: params.get("status") || "",
      priority: params.get("priority") || "",
      ordering: params.get("ordering") || "-updated_at",
    };
  }, [searchParams]);

  const { data, isLoading, isError, error, isFetching } = useQuery({
    queryKey: queryKeys.admin.support.list(queryParams),
    queryFn: () => getSupportTickets(queryParams),
    placeholderData: (previousData) => previousData, // Keeps old data visible while fetching new
    retry: 1,
  });

  const handleFilterChange = (key: string, value: string | null) => {
    const current = new URLSearchParams(Array.from(searchParams.entries()));

    if (value && value.trim() !== "") {
      current.set(key, value);
    } else {
      current.delete(key);
    }

    // When a filter changes, we should go back to the first page
    if (key !== "page") {
      current.delete("page");
    }

    const search = current.toString();
    const query = search ? `?${search}` : "";
    router.push(`${pathname}${query}`);
  };

  if (isLoading) {
    return <SupportTableSkeleton />;
  }

  if (isError) {
    return (
      <Alert variant="destructive">
        <Terminal className="h-4 w-4" />
        <AlertTitle>{t("oops")}</AlertTitle>
        <AlertDescription>
          {(error as Error)?.message || t("generic")}
        </AlertDescription>
      </Alert>
    );
  }

  const pageCount = data ? Math.ceil(data.count / ITEMS_PER_PAGE) : 0;

  return (
    <SupportTable
      data={data?.results ?? []}
      pageCount={pageCount}
      filters={queryParams}
      onFilterChange={handleFilterChange}
      isFetching={isFetching}
    />
  );
}
