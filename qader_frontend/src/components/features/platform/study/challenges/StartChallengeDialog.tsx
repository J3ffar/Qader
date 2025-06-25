"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

import {
  createChallenge,
  getChallengeTypes,
  markAsReady,
} from "@/services/challenges.service";
import { queryKeys } from "@/constants/queryKeys";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { Loader2 } from "lucide-react";
import { PATHS } from "@/constants/paths";
import { useState } from "react";

interface StartChallengeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const formSchema = z.object({
  opponent_username: z
    .string()
    .min(3, "Username must be at least 3 characters.")
    .max(50),
  challenge_type: z.string({
    required_error: "Please select a challenge type.",
  }),
});

export function StartChallengeDialog({
  open,
  onOpenChange,
}: StartChallengeDialogProps) {
  const t = useTranslations("Study.challenges");
  const tCommon = useTranslations("Common");
  const queryClient = useQueryClient();
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
  });

  // Rationale: Fetch challenge types dynamically from the API.
  // This avoids hardcoding and makes the component adaptable to backend changes.
  const { data: challengeTypes, isLoading: isLoadingTypes } = useQuery({
    queryKey: queryKeys.challenges.types(),
    queryFn: getChallengeTypes,
    staleTime: 1000 * 60 * 5, // Cache for 5 minutes
    enabled: open, // Only fetch when the dialog is open
  });

  const createChallengeMutation = useMutation({
    mutationFn: createChallenge,
    onSuccess: async (newChallenge) => {
      toast.promise(markAsReady(newChallenge.id), {
        loading: t("creatingAndPreparing"),
        success: () => {
          queryClient.invalidateQueries({ queryKey: queryKeys.challenges.all });
          router.push(`${PATHS.STUDY.CHALLENGE_COLLEAGUES}/${newChallenge.id}`);
          setIsOpen(false);
          return t("challengeSentAndReady");
        },
        error: (err) => getApiErrorMessage(err, t("Common.errorGeneric")),
      });
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, t("errorGeneric")));
    },
  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    createChallengeMutation.mutate(values);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{t("createChallengeTitle")}</DialogTitle>
          <DialogDescription>
            {t("createChallengeDescription")}
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="space-y-4 pt-4"
          >
            <FormField
              control={form.control}
              name="opponent_username"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("opponentUsername")}</FormLabel>
                  <FormControl>
                    <Input
                      placeholder={t("opponentUsernamePlaceholder")}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="challenge_type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("challengeType")}</FormLabel>
                  {isLoadingTypes ? (
                    <Skeleton className="h-10 w-full" />
                  ) : (
                    <Select
                      onValueChange={field.onChange}
                      defaultValue={field.value}
                      dir="rtl"
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder={t("selectChallengeType")} />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <TooltipProvider>
                          {challengeTypes?.map((type) => (
                            <Tooltip key={type.key} delayDuration={100}>
                              <TooltipTrigger asChild>
                                <SelectItem value={type.key}>
                                  {type.name}
                                </SelectItem>
                              </TooltipTrigger>
                              <TooltipContent side="left" className="max-w-xs">
                                <p>{type.description}</p>
                              </TooltipContent>
                            </Tooltip>
                          ))}
                        </TooltipProvider>
                      </SelectContent>
                    </Select>
                  )}
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <Button
                type="button"
                variant="ghost"
                onClick={() => onOpenChange(false)}
              >
                {tCommon("cancel")}
              </Button>
              <Button
                type="submit"
                disabled={createChallengeMutation.isPending}
              >
                {createChallengeMutation.isPending && (
                  <Loader2 className="ltr:mr-2 rtl:ml-2 h-4 w-4 animate-spin" />
                )}
                {t("startChallenge")}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
