"use client";

import React, { useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { useTranslations } from "next-intl";

import { useConversationStore } from "@/store/conversation.store";
import * as convoService from "@/services/conversation.service";
import { QUERY_KEYS } from "@/constants/queryKeys";

import { ConversationSidebar } from "./ConversationSidebar";
import { ChatWindow } from "./ChatWindow";
import { Card, CardContent } from "@/components/ui/card";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";

export function ConversationLearningClient() {
  const t = useTranslations("Study.conversationalLearning");
  const { sessionId, addMessage, setSessionId, resetConversation } =
    useConversationStore();

  const startConversationMutation = useMutation({
    mutationKey: [QUERY_KEYS.CONVERSATION_START],
    mutationFn: convoService.startConversation,
    onSuccess: (data) => {
      resetConversation(); // Reset state for new session
      setSessionId(data.id);
      // Add initial messages from AI if any
      data.messages.forEach((msg) =>
        addMessage({ type: "text", content: msg })
      );
      toast.success(t("api.startSuccess"));
    },
    onError: (error) => {
      toast.error(t("api.startError"), {
        description: getApiErrorMessage(error, t("api.startError")),
      });
    },
  });

  useEffect(() => {
    // Cleanup on unmount
    return () => {
      resetConversation();
    };
  }, [resetConversation]);

  return (
    <Card>
      <CardContent className="p-4 md:p-6">
        <div className="grid grid-cols-1 gap-4 md:gap-6 lg:grid-cols-4">
          <div className="lg:col-span-1">
            <ConversationSidebar
              onStartConversation={startConversationMutation.mutate}
              isStarting={startConversationMutation.isPending}
            />
          </div>
          <div className="min-h-[600px] lg:col-span-3 lg:min-h-0">
            <ChatWindow />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
