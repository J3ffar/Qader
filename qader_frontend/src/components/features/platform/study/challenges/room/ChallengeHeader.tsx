// src/components/features/platform/study/challenges/room/ChallengeHeader.tsx
"use client";

import { useMemo, useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { User, CheckCircle2 } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Progress } from "@/components/ui/progress";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useAuthCore } from "@/store/auth.store";
import { ChallengeState } from "@/types/api/challenges.types";

interface PlayerInfoProps {
  player: ChallengeState["challenger"] | ChallengeState["opponent"] | null;
  attempt: ChallengeState["attempts"][0] | undefined;
  isCurrentUser: boolean;
  totalQuestions: number;
  answeredCount: number;
  hasJustAnswered: boolean;
}

const PlayerInfo = ({
  player,
  attempt,
  isCurrentUser,
  totalQuestions,
  answeredCount,
  hasJustAnswered,
}: PlayerInfoProps) => {
  const t = useTranslations("Study.challenges");
  if (!player || !attempt) {
    return (
      <div className="flex flex-col items-center gap-2 w-48">
        <Avatar className="h-20 w-20 border-4 border-dashed">
          <AvatarFallback>
            <User className="h-8 w-8 text-muted-foreground" />
          </AvatarFallback>
        </Avatar>
        <p className="font-semibold text-muted-foreground">{t("waiting")}</p>
        <p className="text-2xl font-bold">-</p>
      </div>
    );
  }

  const progressValue =
    totalQuestions > 0 ? (answeredCount / totalQuestions) * 100 : 0;

  return (
    <div className="flex flex-col items-center gap-2 w-48 text-center">
      <div className="relative">
        <Avatar className="h-20 w-20 border-4 border-primary">
          <AvatarImage src={player.profile_picture_url || undefined} />
          <AvatarFallback>
            {player.username.charAt(0).toUpperCase()}
          </AvatarFallback>
        </Avatar>
        <AnimatePresence>
          {hasJustAnswered && (
            <motion.div
              initial={{ scale: 0, y: 10 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0, y: 10 }}
              transition={{ type: "spring", stiffness: 500, damping: 30 }}
              className="absolute -bottom-2 -right-2 bg-green-500 rounded-full p-1 border-2 border-background"
            >
              <CheckCircle2 className="h-5 w-5 text-white" />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
      <p className="text-lg font-bold truncate w-full">
        {player.preferred_name || player.full_name} {isCurrentUser && "(You)"}
      </p>
      <div className="w-full space-y-2">
        <p className="text-2xl font-bold">{attempt.score}</p>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger className="w-full">
              <Progress value={progressValue} />
            </TooltipTrigger>
            <TooltipContent>
              <p>
                {t("answered")} {answeredCount} / {totalQuestions}
              </p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
    </div>
  );
};

interface ChallengeHeaderProps {
  challenge: ChallengeState;
}

export function ChallengeHeader({ challenge }: ChallengeHeaderProps) {
  const { user } = useAuthCore();
  const [lastAnswererId, setLastAnswererId] = useState<number | null>(null);

  useEffect(() => {
    if (challenge.lastAnsweredBy) {
      setLastAnswererId(challenge.lastAnsweredBy);
      const timer = setTimeout(() => setLastAnswererId(null), 2000); // Show indicator for 2s
      return () => clearTimeout(timer);
    }
  }, [challenge.lastAnsweredBy]);

  const challengerAttempt = challenge.attempts.find(
    (att) => att.user.id === challenge.challenger.id
  );
  const opponentAttempt = challenge.attempts.find(
    (att) => att.user.id === challenge.opponent?.id
  );

  const answeredByMap = challenge.answeredBy || {};
  const totalQuestions = challenge.questions.length;
  console.log(totalQuestions);

  const getAnsweredCount = (userId?: number) => {
    if (!userId) return 0;
    return Object.values(answeredByMap).filter((users) =>
      users.includes(userId)
    ).length;
  };

  const challengerAnsweredCount = getAnsweredCount(challenge.challenger.id);
  const opponentAnsweredCount = getAnsweredCount(challenge.opponent?.id);

  return (
    <div className="flex justify-around items-start w-full">
      <PlayerInfo
        player={challenge.challenger}
        attempt={challengerAttempt}
        isCurrentUser={user?.id === challenge.challenger.id}
        totalQuestions={totalQuestions}
        answeredCount={challengerAnsweredCount}
        hasJustAnswered={lastAnswererId === challenge.challenger.id}
      />
      <p className="text-5xl font-extrabold text-muted-foreground pt-6">VS</p>
      <PlayerInfo
        player={challenge.opponent}
        attempt={opponentAttempt}
        isCurrentUser={user?.id === challenge.opponent?.id}
        totalQuestions={totalQuestions}
        answeredCount={opponentAnsweredCount}
        hasJustAnswered={lastAnswererId === challenge.opponent?.id}
      />
    </div>
  );
}
