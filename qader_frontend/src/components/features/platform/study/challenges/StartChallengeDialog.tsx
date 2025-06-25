"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  createChallenge,
  getChallengeTypes,
  markAsReady,
} from "@/services/challenges.service";
import { queryKeys } from "@/constants/queryKeys";
import { PATHS } from "@/constants/paths";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { CreateChallengePayload } from "@/types/api/challenges.types";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface StartChallengeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function StartChallengeDialog({
  open,
  onOpenChange,
}: StartChallengeDialogProps) {
  const t = useTranslations("Study.challenges");
  const tCommon = useTranslations("Common");
  const router = useRouter();
  const queryClient = useQueryClient();
  const [isOpen, setIsOpen] = useState(false);

  // Rationale: Zod schema defines the form validation rules.
  // `opponent_username` is now `z.string().optional()`, making it a non-required field.
  const challengeFormSchema = z.object({
    opponent_username: z.string().optional(),
    challenge_type: z.string({
      required_error: t("errorGeneric"), // A generic error, can be more specific
    }),
  });

  const form = useForm<z.infer<typeof challengeFormSchema>>({
    resolver: zodResolver(challengeFormSchema),
    defaultValues: {
      opponent_username: "",
    },
  });

  const { data: challengeTypes, isLoading: isLoadingTypes } = useQuery({
    queryKey: queryKeys.challenges.types(),
    queryFn: getChallengeTypes,
  });

  const createChallengeMutation = useMutation({
    mutationFn: createChallenge,
    onSuccess: async (newChallenge) => {
      toast.promise(markAsReady(newChallenge.id), {
        loading: t("creatingAndPreparing"),
        success: () => {
          queryClient.invalidateQueries({
            queryKey: queryKeys.challenges.lists(),
          });
          router.push(`${PATHS.STUDY.CHALLENGE_COLLEAGUES}/${newChallenge.id}`);
          setIsOpen(false);
          form.reset();
          return t("challengeSentAndReady");
        },
        error: (err) => getApiErrorMessage(err, t("errorGeneric")),
      });
    },
    onError: (error) => {
      const message = getApiErrorMessage(error, t("errorGeneric"));
      // Display specific backend errors on the form field if possible
      if (message.toLowerCase().includes("user not found")) {
        form.setError("opponent_username", {
          type: "manual",
          message: t("errorUserNotFound"),
        });
      } else {
        toast.error(message);
      }
    },
  });

  function onSubmit(values: z.infer<typeof challengeFormSchema>) {
    const payload: CreateChallengePayload = {
      // Rationale: Ensure that if the optional field is undefined/null, we send an empty string.
      opponent_username: values.opponent_username || "",
      challenge_type: values.challenge_type,
    };
    createChallengeMutation.mutate(payload);
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
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
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
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                    dir="rtl"
                  >
                    <FormControl>
                      <SelectTrigger disabled={isLoadingTypes}>
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
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
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
