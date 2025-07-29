"use client";

import React, { useState } from "react";
import { useTranslations } from "next-intl";
import { Bot, Loader2 } from "lucide-react";
import { AIQuestionResponse } from "@/types/api/conversation.types";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import { QuestionRenderer } from "@/components/shared/QuestionRenderer";
import { RichContentViewer } from "@/components/shared/RichContentViewer";
import { StarButton } from "@/components/shared/StarButton";
import { useConversationStore } from "@/store/conversation.store";

type OptionKey = "A" | "B" | "C" | "D";

const arabicOptionMap: { [key in OptionKey]: string } = {
  A: "أ",
  B: "ب",
  C: "ج",
  D: "د",
};

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
  const { sessionId } = useConversationStore();
  const [selectedAnswer, setSelectedAnswer] = useState<OptionKey | null>(null);
  const [direction, setDirection] = useState<"ltr" | "rtl">("rtl");
  const [localStarred, setLocalStarred] = useState(content.question.is_starred);

  React.useEffect(() => {
    setDirection(document.documentElement.dir as "ltr" | "rtl");
  }, []);

  // Debug: Log question data and sessionId
  console.log("QuestionMessage - AI Chat:", {
    questionId: content.question.id,
    is_starred: content.question.is_starred,
    sessionId,
    questionText: content.question.question_text.substring(0, 50) + "...",
  });

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
      <div className="w-full max-w-xl rounded-lg border bg-card p-4 space-y-4">
        <div className="prose prose-sm dark:prose-invert mb-4 max-w-none">
          <ReactMarkdown>{content.ai_message}</ReactMarkdown>
        </div>

        {/* Question Container with Star Button positioned outside */}
        <div className="flex items-start gap-3">
          {/* Question Container */}
          <div className="flex items-start justify-between w-full border rounded-lg p-4 bg-muted/30">
            <div className="flex-1">
              <QuestionRenderer
                questionText={content.question.question_text}
                imageUrl={content.question.image}
              />
            </div>
              <StarButton
                questionId={content.question.id}
                isStarred={localStarred}
                onStarChange={(newState) => setLocalStarred(newState)}
                disabled={false}
                attemptId={sessionId?.toString() || ""}
              />
          </div>
        </div>

        <RadioGroup
          value={selectedAnswer || ""}
          onValueChange={(value) => setSelectedAnswer(value as OptionKey)}
          className="grid grid-cols-1 gap-3"
          dir={direction}
        >
          {Object.entries(content.question.options).map(([key, text]) => (
            <Label
              key={key}
              htmlFor={`${content.question.id}-${key}`}
              className={cn(
                "flex items-center space-x-3 rtl:space-x-reverse rounded-md border p-3 transition-all",
                "cursor-pointer hover:bg-accent",
                selectedAnswer === key && "border-primary bg-accent"
              )}
            >
              <RadioGroupItem
                value={key}
                id={`${content.question.id}-${key}`}
                className="hidden"
              />
              <div className="flex ml-3 border h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-muted text-sm font-semibold text-muted-foreground">
                {arabicOptionMap[key as OptionKey]}
              </div>
              <RichContentViewer
                htmlContent={text}
                className="prose prose-sm dark:prose-invert max-w-none flex-1"
              />
            </Label>
          ))}
        </RadioGroup>

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
