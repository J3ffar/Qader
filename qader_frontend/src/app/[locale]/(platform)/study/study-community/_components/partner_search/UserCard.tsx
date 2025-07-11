"use client";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { sendPartnerRequest } from "@/services/community.service";
import { User } from "@/types/api/user.types";
import { useMutation } from "@tanstack/react-query";
import { Check, Loader2, UserPlus } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

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
    <Card className="overflow-hidden text-center transition-all hover:shadow-lg">
      <CardContent className="p-6 flex flex-col items-center">
        <Avatar className="h-20 w-20 mb-4 border-2 border-primary/20">
          <AvatarImage src={user.profile_picture_url || undefined} />
          <AvatarFallback className="text-2xl">
            {user.full_name.charAt(0)}
          </AvatarFallback>
        </Avatar>
        <p className="font-bold text-lg">{user.full_name}</p>
        <p className="text-sm text-muted-foreground">{user.grade}</p>
      </CardContent>
      <CardFooter className="">
        <Button
          onClick={handleRequest}
          disabled={mutation.isPending || mutation.isSuccess}
          className={cn(
            "w-full",
            mutation.isSuccess && "bg-green-600 hover:bg-green-700"
          )}
        >
          {mutation.isPending && (
            <Loader2 className="me-2 h-4 w-4 animate-spin" />
          )}
          {mutation.isSuccess && <Check className="me-2 h-4 w-4" />}
          {!mutation.isPending && !mutation.isSuccess && (
            <UserPlus className="me-2 h-4 w-4" />
          )}
          {mutation.isSuccess ? "تم الإرسال" : "طلب زمالة"}
        </Button>
      </CardFooter>
    </Card>
  );
}
