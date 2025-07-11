"use client";

import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "@/constants/queryKeys";
import { getPartnerRequests } from "@/services/community.service";
import { RequestCard } from "./RequestCard";
import { RequestCardSkeleton } from "./RequestCardSkeleton";

export function RequestList({ direction }: { direction: "sent" | "received" }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.community.partnerRequests.list({ direction }),
    queryFn: getPartnerRequests,
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

  if (requests.length === 0) {
    return (
      <p className="text-center text-sm text-muted-foreground py-6">
        {direction === "sent"
          ? "لم تقم بإرسال أي طلبات بعد."
          : "ليس لديك أي طلبات واردة."}
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {requests.map((request) => (
        <RequestCard key={request.id} request={request} direction={direction} />
      ))}
    </div>
  );
}
