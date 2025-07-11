"use client";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { sendPartnerRequest } from "@/services/community.service";
import { User } from "@/types/api/user.types";
import { useMutation } from "@tanstack/react-query";
import { Check, Loader2 } from "lucide-react";
import { toast } from "sonner";

export function UserCard({ user }: { user: User }) {
  const mutation = useMutation({
    mutationFn: () => sendPartnerRequest(user.id),
    onSuccess: () => {
      toast.success(`تم إرسال طلب زميل إلى ${user.full_name}`);
    },
    onError: (error: any) => {
      toast.error("فشل إرسال الطلب", {
        description: error.message || "قد يكون هناك طلب قائم بالفعل.",
      });
    },
  });

  const handleRequest = () => {
    mutation.mutate();
  };

  return (
    <Card className="p-4 flex items-center justify-between">
      <div className="flex items-center space-x-4 rtl:space-x-reverse">
        <Avatar className="h-12 w-12">
          <AvatarImage src={user.profile_picture_url || undefined} />
          <AvatarFallback>{user.full_name.charAt(0)}</AvatarFallback>
        </Avatar>
        <div>
          <p className="font-bold">{user.full_name}</p>
          <p className="text-sm text-muted-foreground">{user.grade}</p>
        </div>
      </div>
      <Button
        onClick={handleRequest}
        disabled={mutation.isPending || mutation.isSuccess}
      >
        {mutation.isPending && (
          <Loader2 className="me-2 h-4 w-4 animate-spin" />
        )}
        {mutation.isSuccess ? <Check className="me-2 h-4 w-4" /> : null}
        {mutation.isSuccess ? "تم الإرسال" : "طلب زمالة"}
      </Button>
    </Card>
  );
}
