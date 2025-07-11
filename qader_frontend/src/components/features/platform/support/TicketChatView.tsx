"use client";

import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import type { SupportTicketDetail } from "@/types/api/support.types";
import { useAuthStore } from "@/store/auth.store";
import { Clock, Check, AlertCircle } from "lucide-react";
import { arSA } from "date-fns/locale";
import { formatDistanceToNow } from "date-fns";

interface TicketChatViewProps {
  ticket: SupportTicketDetail;
}

export function TicketChatView({ ticket }: TicketChatViewProps) {
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const currentUser = useAuthStore((state) => state.user);

  useEffect(() => {
    const viewport = scrollAreaRef.current?.querySelector(
      "[data-radix-scroll-area-viewport]"
    );
    if (viewport) {
      viewport.scrollTop = viewport.scrollHeight;
    }
  }, [ticket.replies]);

  const allMessages = [
    {
      id: `desc-${ticket.id}`,
      user: ticket.user,
      message: ticket.description,
      created_at: ticket.created_at,
      isInitial: true,
    },
    ...ticket.replies,
  ];

  return (
    <ScrollArea className="h-full" ref={scrollAreaRef}>
      <div className="p-4 space-y-6">
        {allMessages.map((reply) => {
          const isCurrentUser = reply.user.id === currentUser?.id;
          const userInitial = (
            reply.user.full_name ||
            reply.user.username ||
            "U"
          )
            .charAt(0)
            .toUpperCase();

          return (
            <div
              key={reply.id}
              className={cn(
                "flex items-end gap-3",
                isCurrentUser ? "justify-end" : "justify-start"
              )}
            >
              {!isCurrentUser && (
                <Avatar className="h-8 w-8">
                  {/* Use the profile picture URL from the API */}
                  <AvatarImage
                    src={reply.user.profile_picture_url || ""}
                    alt={reply.user.full_name || reply.user.username}
                  />
                  <AvatarFallback>{userInitial}</AvatarFallback>
                </Avatar>
              )}
              <div
                className={cn(
                  "max-w-md lg:max-w-xl p-3 rounded-lg relative",
                  isCurrentUser
                    ? "bg-primary text-primary-foreground rounded-br-none"
                    : "bg-muted rounded-bl-none",
                  (reply as any).status === "sending" && "opacity-70",
                  (reply as any).status === "error" && "bg-destructive/80"
                )}
              >
                <p className="whitespace-pre-wrap pb-4">{reply.message}</p>
                <div className="absolute bottom-1.5 ltr:right-2 rtl:left-2 flex items-center gap-1 text-xs opacity-80">
                  {(reply as any).status === "sending" && (
                    <Clock className="h-3 w-3" />
                  )}
                  {(reply as any).status === "error" && (
                    <AlertCircle className="h-3 w-3" />
                  )}
                  <span>
                    {(reply as any).status === "sending"
                      ? "جار الإرسال..."
                      : formatDistanceToNow(new Date(reply.created_at), {
                          addSuffix: true,
                          locale: arSA,
                        })}
                  </span>
                </div>
              </div>
              {isCurrentUser && (
                <Avatar className="h-8 w-8">
                  <AvatarImage
                    src={reply.user.profile_picture_url || ""}
                    alt={reply.user.full_name || reply.user.username}
                  />
                  <AvatarFallback>{userInitial}</AvatarFallback>
                </Avatar>
              )}
            </div>
          );
        })}
      </div>
    </ScrollArea>
  );
}
