"use client";

import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import type { SupportTicketDetail } from "@/types/api/support.types";
import { useAuthStore } from "@/store/auth.store";
import { formatDistanceToNow } from "date-fns";
import { arSA } from "date-fns/locale";

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
    // FIX: The ScrollArea itself is now a flex-grow item
    <ScrollArea className="flex-1" ref={scrollAreaRef}>
      {/* FIX: This div now has h-full to ensure it can scroll within the viewport */}
      <div className="p-4 space-y-6 h-full">
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
                  "max-w-md lg:max-w-xl p-3 rounded-lg",
                  isCurrentUser
                    ? "bg-primary text-primary-foreground rounded-br-none"
                    : "bg-muted rounded-bl-none",
                  (reply as any).optimistic ? "opacity-60" : "" // Style for optimistic messages
                )}
              >
                <p className="whitespace-pre-wrap">{reply.message}</p>
                <p className="text-xs mt-2 opacity-70 text-right">
                  {formatDistanceToNow(new Date(reply.created_at), {
                    addSuffix: true,
                    locale: arSA,
                  })}
                </p>
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
