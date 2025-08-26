"use client";

import React, { useEffect, useState, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { AnimatePresence, motion } from "framer-motion";
import { Check, Loader2, X, Lightbulb, BookOpen, Eye, Clock, AlertTriangle } from "lucide-react";
import { toast } from "sonner";

import { useEmergencyModeStore } from "@/store/emergency.store";
import { submitEmergencyAnswer } from "@/services/study.service";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";

import { cn } from "@/lib/utils";
import {
  UnifiedQuestion,
  EmergencyModeAnswerResponse,
} from "@/types/api/study.types";

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
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
import { queryKeys } from "@/constants/queryKeys";
import { QuestionRenderer } from "@/components/shared/QuestionRenderer";
import { RichContentViewer } from "@/components/shared/RichContentViewer";
import { StarButton } from "@/components/shared/StarButton";

type AnswerOption = "A" | "B" | "C" | "D";

const arabicOptionMap: { [key in AnswerOption]: string } = {
  A: "أ",
  B: "ب",
  C: "ج",
  D: "د",
};

interface QuestionDisplayEmergencyProps {
  question: UnifiedQuestion;
  currentQuestionNumber: number;
  totalQuestions: number;
  isLastQuestion: boolean;
  onLastAnswered: () => void;
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
  questionId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  sessionId: number;
}

const ErrorReportModal: React.FC<ErrorReportModalProps> = ({
  questionId,
  open,
  onOpenChange,
  sessionId,
}) => {
  const [subject, setSubject] = useState("");
  const [problemType, setProblemType] = useState("");
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    
    const reportData = {
      sessionId,
      questionId,
      subject,
      problemType,
      description,
      timestamp: new Date().toISOString(),
    };
    
    console.log("Submitting error report:", reportData);
    
    // Simulate API call - replace with actual API call
    setTimeout(() => {
      setIsSubmitting(false);
      setSubject("");
      setProblemType("");
      setDescription("");
      onOpenChange(false);
      toast.success("تم إرسال البلاغ بنجاح");
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
            <Label htmlFor="subject">موضوع</Label>
            <Input
              id="subject"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="أدخل موضوع المشكلة"
              dir="rtl"
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="problemType">نوع المشكلة</Label>
            <Select value={problemType} onValueChange={setProblemType}>
              <SelectTrigger id="problemType">
                <SelectValue placeholder="اختر نوع المشكلة" />
              </SelectTrigger>
              <SelectContent dir="rtl">
                <SelectItem value="technical">تقني</SelectItem>
                <SelectItem value="question_issue">مشكلة في السؤال</SelectItem>
                <SelectItem value="suggestion">إقتراح</SelectItem>
                <SelectItem value="other">أخرى</SelectItem>
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

// Helper function to extract clean text from HTML
const extractTextFromHTML = (htmlString: string): string => {
  const tempDiv = document.createElement("div");
  tempDiv.innerHTML = htmlString;
  return tempDiv.textContent || tempDiv.innerText || "";
};

export function QuestionDisplayEmergency({
  question,
  currentQuestionNumber,
  totalQuestions,
  isLastQuestion,
  onLastAnswered,
}: QuestionDisplayEmergencyProps) {
  const t = useTranslations("Study.emergencyMode.session.question");
  const { sessionId, goToNextQuestion } = useEmergencyModeStore();

  const [selectedAnswer, setSelectedAnswer] = useState<AnswerOption | null>(null);
  const [isAnswered, setIsAnswered] = useState(false);
  const [feedback, setFeedback] = useState<EmergencyModeAnswerResponse | null>(null);
  const [showHint, setShowHint] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);
  const [showSolution, setShowSolution] = useState(false);
  const [localStarred, setLocalStarred] = useState(question.is_starred);
  const [isErrorModalOpen, setIsErrorModalOpen] = useState(false);

  // Reset component state when a new question is passed in
  useEffect(() => {
    setSelectedAnswer(null);
    setIsAnswered(false);
    setFeedback(null);
    setShowHint(false);
    setShowExplanation(false);
    setShowSolution(false);
    setLocalStarred(question.is_starred);
  }, [question.id, question.is_starred]);

  const { mutate: submitAnswer, isPending } = useMutation({
    mutationKey: queryKeys.emergencyMode.submitAnswer(
      sessionId as number,
      question.id
    ),
    mutationFn: (answer: AnswerOption) =>
      submitEmergencyAnswer({
        sessionId: sessionId!,
        payload: { question_id: question.id, selected_answer: answer },
      }),
    onSuccess: (data) => {
      setFeedback(data);
      setIsAnswered(true);
    },
    onError: (error) => {
      toast.error(t("submitErrorToast"), {
        description: getApiErrorMessage(error, t("submitErrorToast")),
      });
    },
  });

  const handleSubmit = () => {
    if (selectedAnswer) {
      submitAnswer(selectedAnswer);
    }
  };

  const handleNext = () => {
    if (isLastQuestion) {
      onLastAnswered();
    } else {
      goToNextQuestion();
    }
  };

  const options = Object.entries(question.options) as [AnswerOption, string][];

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle>{t("title")}</CardTitle>
              <CardDescription>
                {t("progress", {
                  current: currentQuestionNumber,
                  total: totalQuestions,
                })}
              </CardDescription>
              <div className="mt-4">
                <QuestionRenderer
                  questionText={question.question_text}
                  imageUrl={question.image}
                />
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Timer />
              <StarButton
                questionId={question.id}
                isStarred={localStarred}
                onStarChange={(newState) => setLocalStarred(newState)}
                disabled={isAnswered}
                attemptId={sessionId?.toString() || ""}
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
          </div>
        </CardHeader>
        <CardContent>
          <RadioGroup
            value={selectedAnswer ?? undefined}
            onValueChange={(value: AnswerOption) => setSelectedAnswer(value)}
            disabled={isAnswered || isPending}
            className="space-y-3"
            dir={"rtl"}
          >
            {options.map(([key, value]) => {
              const isSelected = selectedAnswer === key;
              const isCorrect = feedback?.correct_answer === key;
              const wasCorrectlyAnswered = feedback?.is_correct;

              return (
                <div
                  key={key}
                  className={cn(
                    "flex items-center space-x-3 rtl:space-x-reverse rounded-md border p-4 transition-all",
                    "data-[state=checked]:border-primary data-[state=checked]:ring-1 data-[state=checked]:ring-primary",
                    isAnswered && isCorrect && "border-green-500 bg-green-500/10",
                    isAnswered &&
                      isSelected &&
                      !wasCorrectlyAnswered &&
                      "border-red-500 bg-red-500/10",
                    !isAnswered && "cursor-pointer hover:bg-accent"
                  )}
                  data-state={isSelected ? "checked" : "unchecked"}
                  onClick={() =>
                    !(isAnswered || isPending) && setSelectedAnswer(key)
                  }
                >
                  <RadioGroupItem
                    value={key}
                    id={`option-${key}`}
                    className="hidden"
                  />
                  <div className="flex ml-3 border h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-muted text-sm font-semibold text-muted-foreground">
                    {arabicOptionMap[key]}
                  </div>
                  <RichContentViewer
                    htmlContent={value}
                    className="prose dark:prose-invert max-w-none flex-1"
                  />
                </div>
              );
            })}
          </RadioGroup>

          {/* Helper Buttons */}
          <div className="flex flex-wrap gap-2 mt-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowHint(!showHint)}
              className="flex items-center gap-2"
            >
              <Lightbulb className="h-4 w-4" />
              تلميح
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setShowExplanation(!showExplanation);
                setShowSolution(!showSolution);
              }}
              className="flex items-center gap-2"
            >
              <BookOpen className="h-4 w-4" />
              عرض طريقة الحل و الكشف عن الإجابة الصحيحة
            </Button>
          </div>

          {/* Helper Content */}
          <AnimatePresence>
            {showHint && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-4"
              >
                <Alert>
                  <Lightbulb className="h-4 w-4" />
                  <AlertTitle>تلميح</AlertTitle>
                  <AlertDescription>
                    <RichContentViewer
                      htmlContent={question.hint || "لا يوجد تلميح متاح لهذا السؤال"}
                    />
                  </AlertDescription>
                </Alert>
              </motion.div>
            )}
            
            {showExplanation && showSolution && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-4 space-y-4"
              >
                <Alert>
                  <BookOpen className="h-4 w-4" />
                  <AlertTitle>شرح الحل</AlertTitle>
                  <AlertDescription>
                    <RichContentViewer
                      htmlContent={question.explanation || "لا يوجد شرح تفصيلي متاح"}
                    />
                  </AlertDescription>
                </Alert>
                <Alert className="border-green-500">
                  <Eye className="h-4 w-4" />
                  <AlertTitle>الإجابة الصحيحة</AlertTitle>
                  <AlertDescription>
                    <div className="font-bold">
                      {arabicOptionMap[question.correct_answer as AnswerOption]} - 
                      <RichContentViewer
                        htmlContent={question.options[question.correct_answer as AnswerOption]}
                        className="inline"
                      />
                    </div>
                  </AlertDescription>
                </Alert>
              </motion.div>
            )}
          </AnimatePresence>
        </CardContent>
        
        <CardFooter className="flex-col items-stretch space-y-4">
          <AnimatePresence>
            {isAnswered && feedback && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
              >
                <Alert
                  variant={feedback.is_correct ? "default" : "destructive"}
                  className={cn(feedback.is_correct && "border-green-500")}
                >
                  {feedback.is_correct ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    <X className="h-4 w-4" />
                  )}
                  <AlertTitle>
                    {extractTextFromHTML(feedback.feedback)}
                  </AlertTitle>
                  {feedback.explanation && (
                    <AlertDescription className="mt-2">
                      <RichContentViewer htmlContent={feedback.explanation} />
                    </AlertDescription>
                  )}
                </Alert>
              </motion.div>
            )}
          </AnimatePresence>

          {!isAnswered ? (
            <Button
              onClick={handleSubmit}
              disabled={!selectedAnswer || isPending}
              className="w-full"
            >
              {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {t("submitButton")}
            </Button>
          ) : (
            <Button onClick={handleNext} className="w-full">
              {t("nextButton")}
            </Button>
          )}
        </CardFooter>
      </Card>

      {/* Error Report Modal */}
      <ErrorReportModal
        questionId={question.id}
        open={isErrorModalOpen}
        onOpenChange={setIsErrorModalOpen}
        sessionId={sessionId || 0}
      />
    </>
  );
}
