"use client";

import React, { useEffect, useRef } from "react";
import { useTranslations } from "next-intl";
import { Bot } from "lucide-react";

import { useConversationStore } from "@/store/conversation.store";
import { MessageBubble } from "./MessageBubble";
import { ChatInputBar } from "./ChatInputBar";
import { Skeleton } from "@/components/ui/skeleton";

export function ChatWindow() {
  const t = useTranslations("Study.conversationalLearning");
  const { sessionId, messages, isSending } = useConversationStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Auto-scroll to the bottom on new messages
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const renderContent = () => {
    if (!sessionId) {
      return (
        <div className="flex h-full flex-col items-center justify-center text-center">
          <Bot className="mb-4 h-16 w-16 text-muted-foreground" />
          <h3 className="text-xl font-semibold">{t("emptyStateTitle")}</h3>
          <p className="text-muted-foreground">{t("emptyStateDescription")}</p>
        </div>
      );
    }

    if (messages.length === 0 && isSending) {
      return (
        <div className="space-y-4 p-4">
          <Skeleton className="h-16 w-3/4" />
          <div className="flex justify-end">
            <Skeleton className="h-16 w-3/4" />
          </div>
          <Skeleton className="h-16 w-1/2" />
        </div>
      );
    }

    return (
      <div className="flex-1 space-y-4 p-4">
        {messages.map((msg, index) => (
          <MessageBubble
            key={msg.type + (msg.content as any).id + index}
            message={msg}
          />
        ))}
        {isSending && (
          <div className="flex items-center gap-2 p-2 text-sm text-muted-foreground">
            <Bot className="h-5 w-5 animate-pulse" />
            <span>{t("aiTyping")}</span>
          </div>
        )}
        <div ref={scrollRef} />
      </div>
    );
  };

  return (
    <div className="flex h-full flex-col rounded-lg border">
      <div className="flex-1 overflow-y-auto">{renderContent()}</div>
      <ChatInputBar />
    </div>
  );
}
