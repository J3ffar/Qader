import React from "react";
import { useTranslations } from "next-intl";
import { Bot, CheckCircle, Info, XCircle } from "lucide-react";
import ReactMarkdown from "react-markdown";

import { ConversationTestResult } from "@/types/api/conversation.types";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

export const FeedbackMessage = ({
  result,
}: {
  result: ConversationTestResult;
}) => {
  const t = useTranslations("Study.conversationalLearning.session");
  const { is_correct, question, selected_answer, ai_feedback } = result;

  return (
    <div className="flex items-start gap-4">
      <Avatar className="h-9 w-9">
        <AvatarFallback>
          <Bot />
        </AvatarFallback>
      </Avatar>
      <Card className="w-full max-w-xl">
        <CardHeader>
          <CardTitle
            className={cn(
              "flex items-center text-lg font-bold",
              is_correct ? "text-green-600" : "text-red-600"
            )}
          >
            {is_correct ? (
              <CheckCircle className="me-2 h-6 w-6" />
            ) : (
              <XCircle className="me-2 h-6 w-6" />
            )}
            {is_correct ? t("correct") : t("incorrect")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2 rounded-md bg-muted/50 p-3">
            <h4 className="font-semibold">{t("aiFeedback")}</h4>
            <div className="prose prose-sm dark:prose-invert max-w-none text-muted-foreground">
              <ReactMarkdown>{ai_feedback}</ReactMarkdown>
            </div>
          </div>

          <div className="text-sm">
            <p>
              <strong className="font-medium">{t("yourAnswer")}:</strong>{" "}
              {question.options[selected_answer]}
            </p>
            {!is_correct && (
              <p>
                <strong className="font-medium">{t("correctAnswer")}:</strong>{" "}
                {question.options[question.correct_answer]}
              </p>
            )}
          </div>

          {question.explanation && (
            <Accordion type="single" collapsible className="w-full">
              <AccordionItem value="explanation">
                <AccordionTrigger className="text-sm font-medium">
                  <div className="flex items-center">
                    <Info className="me-2 h-4 w-4" /> {t("explanation")}
                  </div>
                </AccordionTrigger>
                <AccordionContent className="prose prose-sm dark:prose-invert max-w-none pt-2 text-muted-foreground">
                  <ReactMarkdown>{question.explanation}</ReactMarkdown>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
