"use client";

import React from "react";
import { useTranslations } from "next-intl";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { BotMessageSquare, SquarePen } from "lucide-react";
import Image from "next/image";

import { useConversationStore } from "@/store/conversation.store";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import {
  sendMessage,
  askForQuestion,
  confirmUnderstanding,
} from "@/services/conversation.service";

import { ConversationSidebar } from "./ConversationSidebar";
import { ConversationInput } from "./ConversationInput";
import { MessageList } from "./MessageList";
import { Button } from "@/components/ui/button";

export const ConversationLearningClient = () => {
  const t = useTranslations("Study.conversationalLearning");
  const {
    sessionId,
    addMessage,
    messages,
    isSending,
    setIsSending,
    setActiveTestQuestion,
  } = useConversationStore();

  const mutationOptions = {
    onMutate: () => setIsSending(true),
    onError: (error: Error) => {
      toast.error(getApiErrorMessage(error, t("api.sendMessageError")));
    },
    onSettled: () => setIsSending(false),
  };

  const sendMessageMutation = useMutation({
    ...mutationOptions,
    mutationFn: (messageText: string) => {
      if (!sessionId) throw new Error("Session ID is missing");
      return sendMessage(sessionId, { message_text: messageText });
    },
    onSuccess: (aiResponse) => {
      addMessage({ type: "text", content: aiResponse });
    },
  });

  const askQuestionMutation = useMutation({
    ...mutationOptions,
    mutationFn: () => {
      if (!sessionId) throw new Error("Session ID is missing");
      return askForQuestion(sessionId);
    },
    onSuccess: (data) => {
      // API now sends a question inside a message wrapper
      addMessage({ type: "question", content: data, sender: "ai" });
    },
  });

  const confirmUnderstandingMutation = useMutation({
    ...mutationOptions,
    mutationFn: () => {
      if (!sessionId) throw new Error("Session ID is missing");
      return confirmUnderstanding(sessionId);
    },
    onSuccess: (data) => {
      if (data && "ai_message" in data) {
        // Check if API returned a test question
        // This now becomes a special "question" type message
        addMessage({
          type: "question",
          content: {
            ai_message: data.ai_message,
            question: data.test_question,
          },
          sender: "ai",
        });
      }
      // If the response is empty (204 No Content), do nothing.
    },
  });

  const handleSendMessage = (message: string) => {
    // Optimistically add user message
    const userMessage = {
      id: Date.now(),
      sender_type: "user" as const,
      message_text: message,
      related_question_id: null,
      timestamp: new Date().toISOString(),
    };
    addMessage({ type: "text", content: userMessage });
    sendMessageMutation.mutate(message);
  };

  return (
    <div className="flex flex-col md:h-screen max-h-full">
      <div className="flex flex-col p-4 m-4">
        <p className="text-center text-xl font-semibold sm:self-start">
          {t("title")}
        </p>
        <p className="text-center text-muted-foreground sm:self-start">
          {t("description")}
        </p>
      </div>
      <div className="flex flex-1 flex-col md:flex-row-reverse w-full min-w-0 mb-8">
        <ConversationSidebar
          isSending={isSending}
          onSendMessage={handleSendMessage}
          onAskForQuestion={() => askQuestionMutation.mutate()}
          onConfirmUnderstanding={() => confirmUnderstandingMutation.mutate()}
        />

        <div className="w-full md:w-full min-w-2/5 border rounded-2xl h-full flex flex-col dark:bg-[#0B1739]">
          <div className="flex-1 px-2 pb-2 overflow-y-auto">
            <div className="max-h-[calc(100vh-14rem)] overflow-y-auto ">
              {messages.length === 0 ? (
                <div className="flex flex-col min-w-fit items-center my-32">
                  <Image
                    src="/images/chat.svg"
                    alt="Chat image"
                    width={250}
                    height={250}
                    className="object-contain"
                  />
                  <h2 className="mt-4 text-2xl font-semibold">
                    {t("emptyStateTitle")}
                  </h2>
                  <p className="mt-2 text-muted-foreground">
                    {t("emptyStateDescription")}
                  </p>
                </div>
              ) : (
                <MessageList />
              )}
            </div>
          </div>

          <div className="border-sm">
            <ConversationInput
              isSending={isSending}
              onSendMessage={handleSendMessage}
              onAskForQuestion={() => askQuestionMutation.mutate()}
              onConfirmUnderstanding={() =>
                confirmUnderstandingMutation.mutate()
              }
            />
          </div>
        </div>
      </div>
    </div>
  );
};
