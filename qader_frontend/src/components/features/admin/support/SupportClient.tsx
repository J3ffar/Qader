"use client";

import { useMemo } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { getSupportTickets } from "@/services/api/admin/support.service";
import { queryKeys } from "@/constants/queryKeys";
import { SupportTableSkeleton } from "./SupportTableSkeleton";
import { SupportTable } from "./SupportTable"; // We'll create this next
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Terminal } from "lucide-react";

export function SupportClient() {
  const t = useTranslations("Admin.support");
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

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

  const { data, isLoading, isError, error } = useQuery({
    queryKey: queryKeys.admin.support.list(queryParams),
    queryFn: () => getSupportTickets(queryParams),
  });

  const handleFilterChange = (key: string, value: string | null) => {
    const params = new URLSearchParams(searchParams);
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    // Reset to first page when filters change, except for pagination itself
    if (key !== "page") {
      params.delete("page");
    }
    router.push(`${pathname}?${params.toString()}`);
  };

  if (isLoading) {
    return <SupportTableSkeleton />;
  }

  if (isError) {
    return (
      <Alert variant="destructive">
        <Terminal className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>
          {(error as Error)?.message || t("actions.deleteError")}
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <SupportTable
      data={data?.results ?? []}
      pageCount={data ? Math.ceil(data.count / 10) : 0} // Assuming 10 items per page
      filters={queryParams}
      onFilterChange={handleFilterChange}
    />
  );
}
