"use client";

import React, { useState, useEffect, useRef } from "react";
import { useTranslations } from "next-intl";
import { CheckCircle, Info, Lightbulb, XCircle, Clock, AlertTriangle, Check } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import type { UnifiedQuestion } from "@/types/api/study.types";
import { QuestionState } from "./TraditionalLearningSession";
import { QuestionRenderer } from "@/components/shared/QuestionRenderer";
import { RichContentViewer } from "@/components/shared/RichContentViewer";
import { StarButton } from "@/components/shared/StarButton";

type OptionKey = "A" | "B" | "C" | "D";

const arabicOptionMap: { [key in OptionKey]: string } = {
  A: "أ",
  B: "ب",
  C: "ج",
  D: "د",
};

interface Props {
  question: UnifiedQuestion;
  questionState?: QuestionState;
  onSelectAnswer: (selectedAnswer: OptionKey) => void;
  direction: "ltr" | "rtl";
  attemptId: string;
}

// Timer Component
const Timer: React.FC = () => {
  const [seconds, setSeconds] = useState(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    intervalRef.current = setInterval(() => {
      setSeconds((prev) => prev + 1);
    }, 1000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  const formatTime = (totalSeconds: number) => {
    const minutes = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${minutes.toString().padStart(2, "0")}:${secs
      .toString()
      .padStart(2, "0")}`;
  };

  return (
    <div className="flex items-center gap-1 text-sm text-muted-foreground">
      <Clock className="h-4 w-4" />
      <span className="font-mono">{formatTime(seconds)}</span>
    </div>
  );
};

// Error Report Modal Component
interface ErrorReportModalProps {
  questionId: any;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const ErrorReportModal: React.FC<ErrorReportModalProps> = ({
  questionId,
  open,
  onOpenChange,
}) => {
  const [subject, setSubject] = useState("");
  const [problemType, setProblemType] = useState("");
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    
    // Here you would typically send the error report to your API
    const reportData = {
      questionId,
      subject,
      problemType,
      description,
      timestamp: new Date().toISOString(),
    };
    
    // Simulate API call
    console.log("Submitting error report:", reportData);
    
    // You would replace this with actual API call:
    // await submitErrorReport(reportData);
    
    setTimeout(() => {
      setIsSubmitting(false);
      // Reset form
      setSubject("");
      setProblemType("");
      setDescription("");
      onOpenChange(false);
      // You might want to show a success toast here
    }, 1000);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]" dir="rtl">
        <DialogHeader>
          <DialogTitle>إبلاغ عن خطأ</DialogTitle>
          <DialogDescription>
            ساعدنا في تحسين المحتوى بالإبلاغ عن أي مشكلة واجهتها
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          
          <div className="grid gap-2">
            <Label htmlFor="problemType">نوع المشكلة</Label>
            <Select value={problemType} onValueChange={setProblemType}>
              <SelectTrigger id="problemType">
                <SelectValue placeholder="مشكلة في السؤال" />
              </SelectTrigger>
              <SelectContent dir="rtl">
                <SelectItem value="question_issue" defaultChecked>مشكلة في السؤال</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="grid gap-2">
            <Label htmlFor="description">وصف المشكلة</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="اشرح المشكلة بالتفصيل..."
              className="min-h-[100px]"
              dir="rtl"
            />
          </div>
        </div>
        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isSubmitting}
          >
            إلغاء
          </Button>
          <Button
            type="submit"
            onClick={handleSubmit}
            disabled={!subject || !problemType || !description || isSubmitting}
          >
            {isSubmitting ? "جاري الإرسال..." : "إرسال"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export const QuestionDisplay: React.FC<Props> = ({
  question,
  questionState,
  onSelectAnswer,
  direction,
  attemptId,
}) => {
  const t = useTranslations("Study.traditionalLearning.session");
  const [localStarred, setLocalStarred] = useState(question.is_starred);
  const [isErrorModalOpen, setIsErrorModalOpen] = useState(false);
  
  // New state for handling answer confirmation
  const [selectedAnswer, setSelectedAnswer] = useState<OptionKey | null>(null);
  const [isConfirmed, setIsConfirmed] = useState(false);

  // Update localStarred when question changes
  useEffect(() => {
    setLocalStarred(question.is_starred);
  }, [question.id, question.is_starred]);

  // Reset confirmation state when question changes
  useEffect(() => {
    setSelectedAnswer(null);
    setIsConfirmed(false);
  }, [question.id]);

  const isAnswered =
    questionState?.status === "correct" ||
    questionState?.status === "incorrect";

  const handleAnswerSelection = (value: OptionKey) => {
    if (!isAnswered && !isConfirmed) {
      setSelectedAnswer(value);
    }
  };

  const handleConfirmAnswer = () => {
    if (selectedAnswer && !isConfirmed) {
      setIsConfirmed(true);
      onSelectAnswer(selectedAnswer);
    }
  };

  const handleChangeAnswer = () => {
    setSelectedAnswer(null);
    setIsConfirmed(false);
  };

  return (
    <>
      <Card className="shadow-lg">
        <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-4">
          <div className="flex-1">
            <QuestionRenderer
              questionText={question.question_text}
              imageUrl={question.image}
            />
          </div>
          <div className="flex items-center gap-3">
            <Timer />
            <StarButton
              questionId={question.id}
              isStarred={localStarred}
              onStarChange={(newState) => setLocalStarred(newState)}
              disabled={isAnswered}
              attemptId={attemptId}
            />
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsErrorModalOpen(true)}
              className="flex items-center gap-2"
            >
              <AlertTriangle className="h-4 w-4" />
              <span>إبلاغ عن خطأ</span>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <RadioGroup
            value={isConfirmed ? (questionState?.selectedAnswer || "") : (selectedAnswer || "")}
            onValueChange={(value) => handleAnswerSelection(value as OptionKey)}
            className="grid grid-cols-1 gap-3 md:grid-cols-2"
            dir={direction}
            disabled={isAnswered || isConfirmed}
          >
            {Object.entries(question.options).map(([key, text]) => {
              const optionKey = key as OptionKey;
              const isSelected = isConfirmed ? 
                (questionState?.selectedAnswer === optionKey) : 
                (selectedAnswer === optionKey);
              const isCorrectOption = question.correct_answer === optionKey;
              const isEliminated =
                questionState?.eliminatedOptions?.includes(optionKey);
              const isRevealedAnswer =
                questionState?.revealedAnswer === optionKey;

              let variant: "default" | "correct" | "incorrect" = "default";
              if (isAnswered) {
                if (isCorrectOption) variant = "correct";
                else if (questionState?.selectedAnswer === optionKey) variant = "incorrect";
              }

              const uniqueId = `${question.id}-${optionKey}`;

              return (
                <Label
                  key={uniqueId}
                  htmlFor={uniqueId}
                  className={cn(
                    "flex items-center space-x-3 rtl:space-x-reverse rounded-md border p-4 transition-all",
                    (isAnswered || isEliminated || isConfirmed)
                      ? "cursor-not-allowed opacity-60"
                      : "cursor-pointer hover:bg-accent",
                    isEliminated && "bg-muted line-through",
                    isSelected && !isAnswered && "border-primary bg-accent",
                    variant === "correct" &&
                      "border-green-500 bg-green-500/10 opacity-100",
                    variant === "incorrect" &&
                      "border-red-500 bg-red-500/10 opacity-100",
                    isRevealedAnswer &&
                      !isAnswered &&
                      "border-blue-500 ring-2 ring-blue-500 ring-offset-2 dark:ring-offset-background"
                  )}
                >
                  <RadioGroupItem
                    value={optionKey}
                    id={uniqueId}
                    disabled={isEliminated || isConfirmed}
                    className="hidden"
                  />
                  <div className="flex ml-3 border h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-muted text-sm font-semibold text-muted-foreground">
                    {arabicOptionMap[optionKey]}
                  </div>
                  <RichContentViewer
                    htmlContent={text}
                    className="prose dark:prose-invert max-w-none flex-1"
                  />
                </Label>
              );
            })}
          </RadioGroup>

          {/* Confirmation Button Section */}
          {selectedAnswer && !isAnswered && !isConfirmed && (
            <div className="mt-4 flex flex-col gap-3 items-center p-4 bg-blue-50 dark:bg-blue-950/20 rounded-lg border border-blue-200 dark:border-blue-800">
              <div className="text-center">
                <p className="text-sm text-muted-foreground mb-2">
                  لقد اخترت الإجابة: <strong className="text-foreground">{arabicOptionMap[selectedAnswer]}</strong>
                </p>
                <p className="text-xs text-muted-foreground">
                  تأكد من إجابتك قبل التأكيد - لن تتمكن من تغييرها لاحقاً
                </p>
              </div>
              <div className="flex gap-2">
                <Button 
                  onClick={handleConfirmAnswer}
                  className="bg-green-600 hover:bg-green-700 text-white"
                  size="sm"
                >
                  <Check className="me-2 h-4 w-4" />
                  تأكيد الإجابة
                </Button>
                <Button 
                  onClick={handleChangeAnswer}
                  variant="outline"
                  size="sm"
                >
                  تغيير الإجابة
                </Button>
              </div>
            </div>
          )}

          {/* --- Post-Answer Feedback Section --- */}
          {isAnswered && (
            <div className="mt-6 space-y-4">
              <Separator />
              {questionState?.status === "correct" && (
                <Badge variant="default" className="bg-green-600 text-base">
                  <CheckCircle className="me-2 h-4 w-4" /> {t("correct")}
                </Badge>
              )}
              {questionState?.status === "incorrect" && (
                <div className="space-y-2">
                  <Badge variant="destructive" className="text-base">
                    <XCircle className="me-2 h-4 w-4" />
                    {t("incorrect")}
                  </Badge>
                  <p className="text-sm text-muted-foreground">
                    {t("correctAnswerWas")}{" "}
                    <strong className="text-foreground">
                      <RichContentViewer
                        htmlContent={
                          question.options[
                            question.correct_answer as keyof typeof question.options
                          ]
                        }
                      />
                    </strong>
                  </p>
                </div>
              )}
            </div>
          )}

          {/* --- Revealed Hint/Explanation Section --- */}
          {questionState?.revealedHint && (
            <Alert className="mt-4 border-yellow-500/50 text-yellow-800 dark:text-yellow-300">
              <Lightbulb className="h-5 w-5 !text-yellow-500" />
              <AlertTitle>{t("controls.hint")}</AlertTitle>
              <AlertDescription>
                <RichContentViewer
                  htmlContent={questionState.revealedHint}
                  className="prose prose-sm dark:prose-invert max-w-none"
                />
              </AlertDescription>
            </Alert>
          )}
          {questionState?.revealedExplanation && (
            <Alert className="mt-4 border-blue-500/50">
              <Info className="h-5 w-5 !text-blue-500" />
              <AlertTitle>{t("explanation")}</AlertTitle>
              <AlertDescription>
                <RichContentViewer
                  htmlContent={questionState.revealedExplanation}
                  className="prose prose-sm dark:prose-invert max-w-none"
                />
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Error Report Modal */}
      <ErrorReportModal
        questionId={question.id}
        open={isErrorModalOpen}
        onOpenChange={setIsErrorModalOpen}
      />
    </>
  );
};
