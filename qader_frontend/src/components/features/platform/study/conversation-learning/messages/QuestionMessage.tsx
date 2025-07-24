"use client";

import React, { useState } from "react";
import { useTranslations } from "next-intl";
import { Bot, Loader2 } from "lucide-react";
import { QuestionDisplay } from "../../traditional-learning/QuestionDisplay"; // Reusing component
import { AIQuestionResponse } from "@/types/api/conversation.types";
import { UnifiedQuestion } from "@/types/api/study.types";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import ReactMarkdown from "react-markdown";

type OptionKey = "A" | "B" | "C" | "D";

interface Props {
  content: AIQuestionResponse;
  onSubmitAnswer: (questionId: number, answer: OptionKey) => void;
  isSubmitting: boolean;
}

export const QuestionMessage: React.FC<Props> = ({
  content,
  onSubmitAnswer,
  isSubmitting,
}) => {
  const t = useTranslations("Study.conversationalLearning.session");
  const [selectedAnswer, setSelectedAnswer] = useState<OptionKey | null>(null);
  const [direction, setDirection] = useState<"ltr" | "rtl">("ltr");

  React.useEffect(() => {
    setDirection(document.documentElement.dir as "ltr" | "rtl");
  }, []);

  const handleSubmit = () => {
    if (selectedAnswer) {
      onSubmitAnswer(content.question.id, selectedAnswer);
    }
  };

  return (
    <div className="flex items-start gap-4">
      <Avatar className="h-9 w-9">
        <AvatarFallback>
          <Bot />
        </AvatarFallback>
      </Avatar>
      <div className="w-full max-w-xl rounded-lg border bg-card p-4">
        <div className="prose prose-sm dark:prose-invert mb-4 max-w-none">
          <ReactMarkdown>{content.ai_message}</ReactMarkdown>
        </div>
        <QuestionDisplay
          question={content.question}
          onSelectAnswer={(answer) => setSelectedAnswer(answer)}
          direction={direction}
          questionState={{
            status: "unanswered",
            selectedAnswer: selectedAnswer,
          }}
        />
        <div className="mt-4 flex justify-end">
          <Button
            onClick={handleSubmit}
            disabled={!selectedAnswer || isSubmitting}
            className="cursor-pointer"
          >
            {isSubmitting && <Loader2 className="me-2 h-4 w-4 animate-spin" />}
            {t("submitAnswer")}
          </Button>
        </div>
      </div>
    </div>
  );
};
