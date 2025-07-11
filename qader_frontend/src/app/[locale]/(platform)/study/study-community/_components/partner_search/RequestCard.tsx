"use client";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { queryKeys } from "@/constants/queryKeys";
import {
  acceptPartnerRequest,
  rejectPartnerRequest,
} from "@/services/community.service";
import { PartnerRequest, RequestStatus } from "@/types/api/community.types";
import { SimpleUser } from "@/types/api/user.types";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Check, Clock, Loader2, X } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

const STATUS_CONFIG: Record<
  RequestStatus,
  { text: string; className: string; icon: React.ReactNode }
> = {
  pending: {
    text: "قيد الانتظار",
    className: "bg-amber-500",
    icon: <Clock className="me-1 h-3 w-3" />,
  },
  accepted: {
    text: "مقبول",
    className: "bg-green-600",
    icon: <Check className="me-1 h-3 w-3" />,
  },
  rejected: {
    text: "مرفوض",
    className: "bg-red-600",
    icon: <X className="me-1 h-3 w-3" />,
  },
};

interface RequestCardProps {
  request: PartnerRequest;
  direction: "sent" | "received";
}

export function RequestCard({ request, direction }: RequestCardProps) {
  const queryClient = useQueryClient();
  const userToShow: SimpleUser =
    direction === "sent" ? request.to_user : request.from_user;
  const queryKey = queryKeys.community.partnerRequests.list({ direction });

  const handleMutation = (
    mutationFn: (id: number) => Promise<PartnerRequest>,
    newStatus: RequestStatus
  ) => {
    return useMutation({
      mutationFn: () => mutationFn(request.id),
      onMutate: async () => {
        await queryClient.cancelQueries({ queryKey });
        const previousRequests = queryClient.getQueryData<any>(queryKey);

        queryClient.setQueryData(queryKey, (oldData: any) => ({
          ...oldData,
          results: oldData.results.map((r: PartnerRequest) =>
            r.id === request.id ? { ...r, status: newStatus } : r
          ),
        }));
        return { previousRequests };
      },
      onError: (err, variables, context) => {
        queryClient.setQueryData(queryKey, context?.previousRequests);
        toast.error("حدث خطأ ما، يرجى المحاولة مرة أخرى.");
      },
      onSettled: () => {
        queryClient.invalidateQueries({
          queryKey: queryKeys.community.partnerRequests.all(),
        });
      },
    });
  };

  const acceptMutation = handleMutation(acceptPartnerRequest, "accepted");
  const rejectMutation = handleMutation(rejectPartnerRequest, "rejected");

  const renderActions = () => {
    if (direction === "received" && request.status === "pending") {
      const isLoading = acceptMutation.isPending || rejectMutation.isPending;
      return (
        <div className="flex gap-2">
          <Button
            size="sm"
            onClick={() => acceptMutation.mutate()}
            disabled={isLoading}
          >
            {acceptMutation.isPending && (
              <Loader2 className="me-2 h-4 w-4 animate-spin" />
            )}{" "}
            قبول
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => rejectMutation.mutate()}
            disabled={isLoading}
          >
            {rejectMutation.isPending && (
              <Loader2 className="me-2 h-4 w-4 animate-spin" />
            )}{" "}
            رفض
          </Button>
        </div>
      );
    }
    return null;
  };

  return (
    <Card className="p-3 flex items-center justify-between">
      <div className="flex items-center space-x-4 rtl:space-x-reverse">
        <Avatar className="h-10 w-10">
          <AvatarImage src={userToShow.profile_picture_url || undefined} />
          <AvatarFallback>{userToShow.full_name?.charAt(0)}</AvatarFallback>
        </Avatar>
        <div>
          <p className="font-semibold">{userToShow.full_name}</p>
          <p className="text-sm text-muted-foreground">{userToShow.grade}</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Badge
          className={cn("text-white", STATUS_CONFIG[request.status].className)}
        >
          {STATUS_CONFIG[request.status].icon}
          {STATUS_CONFIG[request.status].text}
        </Badge>
        {renderActions()}
      </div>
    </Card>
  );
}
