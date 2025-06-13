import React from "react";
import { useTranslations } from "next-intl";
import { Check, X } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Props {
  correct: number;
  incorrect: number;
}

export const SessionStats: React.FC<Props> = ({ correct, incorrect }) => {
  const t = useTranslations("Study.traditionalLearning.session");

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("sessionStatsTitle")}</CardTitle>
      </CardHeader>
      <CardContent className="flex justify-around text-center">
        <div>
          <p className="flex items-center justify-center text-3xl font-bold text-green-600">
            <Check className="me-2 h-7 w-7" />
            {correct}
          </p>
          <p className="text-sm text-muted-foreground">{t("correctAnswers")}</p>
        </div>
        <div>
          <p className="flex items-center justify-center text-3xl font-bold text-red-600">
            <X className="me-2 h-7 w-7" />
            {incorrect}
          </p>
          <p className="text-sm text-muted-foreground">
            {t("incorrectAnswers")}
          </p>
        </div>
      </CardContent>
    </Card>
  );
};
