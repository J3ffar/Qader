"use client";

import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "@/constants/queryKeys";
import { getPartnerRequests } from "@/services/community.service";
import { RequestCard } from "./RequestCard";
import { RequestCardSkeleton } from "./RequestCardSkeleton";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";

export function RequestList({ direction }: { direction: "sent" | "received" }) {
  const [page, setPage] = useState(1);

  const { data, isLoading, isError, isFetching } = useQuery({
    queryKey: queryKeys.community.partnerRequests.list({ direction, page }),
    queryFn: getPartnerRequests,
    placeholderData: (previousData) => previousData, // keep old data visible while fetching new
  });

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <RequestCardSkeleton key={i} />
        ))}
      </div>
    );
  }
  if (isError) {
    return (
      <p className="text-center text-sm text-destructive py-6">
        فشل في تحميل الطلبات.
      </p>
    );
  }

  const requests = data?.results ?? [];
  const hasPrevious = data?.previous !== null;
  const hasNext = data?.next !== null;

  return (
    <div>
      {requests.length === 0 ? (
        <p className="text-center text-sm text-muted-foreground py-6">
          {direction === "sent"
            ? "لم تقم بإرسال أي طلبات بعد."
            : "ليس لديك أي طلبات واردة."}
        </p>
      ) : (
        <div className="space-y-3">
          {requests.map((request) => (
            <RequestCard
              key={request.id}
              request={request}
              direction={direction}
            />
          ))}
        </div>
      )}

      {(hasPrevious || hasNext) && (
        <div className="flex items-center justify-center gap-4 mt-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => p - 1)}
            disabled={!hasPrevious || isFetching}
          >
            <ChevronRight className="h-4 w-4" />
            السابق
          </Button>
          <span className="text-sm font-bold">صفحة {page}</span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => p + 1)}
            disabled={!hasNext || isFetching}
          >
            التالي
            <ChevronLeft className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
