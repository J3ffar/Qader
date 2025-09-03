"use client";

import React, { useRef, useEffect } from "react";
import { useTranslations } from "next-intl";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useConversationStore } from "@/store/conversation.store";
import { submitConversationTestAnswer } from "@/services/conversation.service";
import { CustomMessageType } from "@/types/api/conversation.types";

import { TextMessage } from "./messages/TextMessage";
import { QuestionMessage } from "./messages/QuestionMessage";
import { FeedbackMessage } from "./messages/FeedbackMessage";

export const MessageList = () => {
  const t = useTranslations("Study.conversationalLearning");
  const { messages, sessionId, addMessage, setIsSending, isSending } =
    useConversationStore();
  const queryClient = useQueryClient();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  const submitAnswerMutation = useMutation({
    mutationFn: (payload: {
      questionId: number;
      selectedAnswer: "A" | "B" | "C" | "D";
    }) => {
      if (!sessionId) throw new Error("Session ID is missing");
      return submitConversationTestAnswer(sessionId, {
        question_id: payload.questionId,
        selected_answer: payload.selectedAnswer,
      });
    },
    onMutate: () => setIsSending(true),
    onSuccess: (data) => {
      addMessage({ type: "feedback", content: data, sender: "ai" });
    },
    onError: () => {
      /* Handled in ConversationLearningClient */
    },
    onSettled: () => setIsSending(false),
  });

  const handleSubmitAnswer = (
    questionId: number,
    selectedAnswer: "A" | "B" | "C" | "D"
  ) => {
    submitAnswerMutation.mutate({ questionId, selectedAnswer });
  };

  const renderMessage = (msg: CustomMessageType, index: number) => {
    switch (msg.type) {
      case "text":
        return (
          <TextMessage
            key={`text-${msg.content.id ?? "no_id"}-${index}`}
            message={msg.content}
          />
        );
      case "question":
        // For questions, we need to pass down the submission handler
        return (
          <QuestionMessage
            key={`q-${msg.content.question.id ?? "no_id"}-${index}`}
            content={msg.content}
            onSubmitAnswer={handleSubmitAnswer}
            isSubmitting={submitAnswerMutation.isPending}
          />
        );
      case "feedback":
        return (
          <FeedbackMessage
            key={`fb-${msg.content.id ?? "no_id"}-${index}`}
            result={msg.content}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="flex-1 overflow-y-auto max-md:px-0 p-6">
      <div className="mx-auto max-w-4xl space-y-6">
        {messages.map(renderMessage)}
        {isSending && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <div className="h-2 w-2 animate-pulse rounded-full bg-muted-foreground" />
            <div className="h-2 w-2 animate-pulse rounded-full bg-muted-foreground [animation-delay:0.2s]" />
            <div className="h-2 w-2 animate-pulse rounded-full bg-muted-foreground [animation-delay:0.4s]" />
            <span>{t("aiTyping")}</span>
          </div>
        )}
        <div ref={scrollRef} />
      </div>
    </div>
  );
};
