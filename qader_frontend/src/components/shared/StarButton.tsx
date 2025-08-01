"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Star } from "lucide-react";
import { cn } from "@/lib/utils";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { starQuestion, unstarQuestion } from "@/services/learning.service";
import { queryKeys } from "@/constants/queryKeys";

interface StarButtonProps {
  questionId: number;
  isStarred: boolean;
  onStarChange?: (newState: boolean) => void;
  disabled?: boolean;
  attemptId: string;
}

export const StarButton: React.FC<StarButtonProps> = ({
  questionId,
  isStarred,
  onStarChange,
  disabled = false,
  attemptId,
}) => {
  const queryClient = useQueryClient();

  // Helper function to update star status in a question object
  const updateQuestionInData = (data: any, newStarredStatus: boolean) => {
    if (!data) return data;

    // Handle array of questions
    if (Array.isArray(data)) {
      return data.map((q: any) =>
        q.id === questionId ? { ...q, is_starred: newStarredStatus } : q
      );
    }

    // Handle test attempt response (most common case)
    if (data.included_questions && Array.isArray(data.included_questions)) {
      return {
        ...data,
        included_questions: data.included_questions.map((q: any) =>
          q.id === questionId ? { ...q, is_starred: newStarredStatus } : q
        ),
      };
    }

    // Handle single question response
    if (data.id === questionId) {
      return { ...data, is_starred: newStarredStatus };
    }

    return data;
  };

  // Only update what's actually needed
  const updateCaches = (newStarredStatus: boolean) => {
    // Update test attempt cache (used in traditional learning, tests, determine level)
    queryClient.setQueriesData(
      { queryKey: queryKeys.tests.detail(attemptId) },
      (oldData: any) => updateQuestionInData(oldData, newStarredStatus)
    );
    // Invalidate test review cache
    queryClient.invalidateQueries({
      queryKey: queryKeys.tests.review(attemptId),
    });

    // Invalidate all tests cache
    queryClient.invalidateQueries({
      queryKey: queryKeys.tests.details(),
    });
  };

  const starMutation = useMutation({
    mutationFn: () => starQuestion(questionId),
    onMutate: async () => {
      await queryClient.cancelQueries({
        queryKey: queryKeys.tests.detail(attemptId),
      });

      const previousData = queryClient.getQueryData(
        queryKeys.tests.detail(attemptId)
      );

      updateCaches(true);

      return { previousData };
    },
    onError: (err, variables, context) => {
      if (context?.previousData) {
        queryClient.setQueryData(
          queryKeys.tests.detail(attemptId),
          context.previousData
        );
      }
      toast.error(getApiErrorMessage(err, "فشل ..."));
    },
    onSuccess: () => {
      onStarChange?.(true);
    },
  });

  const unstarMutation = useMutation({
    mutationFn: () => unstarQuestion(questionId),
    onMutate: async () => {
      await queryClient.cancelQueries({
        queryKey: queryKeys.tests.detail(attemptId),
      });

      const previousData = queryClient.getQueryData(
        queryKeys.tests.detail(attemptId)
      );

      updateCaches(false);

      return { previousData };
    },
    onError: (err, variables, context) => {
      if (context?.previousData) {
        queryClient.setQueryData(
          queryKeys.tests.detail(attemptId),
          context.previousData
        );
      }
      toast.error(getApiErrorMessage(err, "فشل ..."));
    },
    onSuccess: () => {
      onStarChange?.(false);
    },
  });

  const handleToggle = () => {
    if (disabled) return;
    isStarred ? unstarMutation.mutate() : starMutation.mutate();
  };

  const isPending = starMutation.isPending || unstarMutation.isPending;

  return (
    <button
      onClick={handleToggle}
      disabled={disabled || isPending}
      className={cn(
        "inline-flex items-center justify-center rounded-full transition-all duration-200",
        "hover:scale-105 focus:outline-none focus:ring-2 focus:ring-offset-2",
        "disabled:cursor-not-allowed disabled:opacity-50",
        "h-6 w-6 lg:h-10 lg:w-10",
        "bg-background/80 backdrop-blur-sm lg:border lg:border-border/50",
        isStarred
          ? "text-yellow-500 hover:text-yellow-600 focus:ring-yellow-500 hover:bg-yellow-50/50"
          : "text-gray-400 hover:text-yellow-500 focus:ring-gray-400 hover:bg-gray-50/50"
      )}
      aria-label={
        isStarred ? `إزالة السؤال من المفضلة` : `إضافة السؤال للمفضلة`
      }
    >
      <Star
        className={cn(
          "h-4 w-4 md:w-5 md:h-5 transition-all duration-200 cursor-pointer",
          isStarred ? "fill-current" : "fill-none",
          isPending && "animate-pulse"
        )}
      />
    </button>
  );
};
