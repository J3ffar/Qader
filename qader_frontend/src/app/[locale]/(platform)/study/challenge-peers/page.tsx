import { ChallengesDashboard } from "@/components/features/platform/study/challenges/ChallengesDashboard";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { getTranslations } from "next-intl/server";
import { Swords } from "lucide-react";

export default async function ChallengePeersPage() {
  const t = await getTranslations("Study.challenges");

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row justify-end items-center gap-4 rtl:flex-row-reverse">
          <div>
            <CardTitle>{t("title")}</CardTitle>
            <CardDescription>{t("description")}</CardDescription>
          </div>
          <div className="bg-primary/10 p-3 rounded-lg">
            <Swords className="h-6 w-6 text-primary" />
          </div>
        </CardHeader>
      </Card>
      <ChallengesDashboard />
    </div>
  );
}
