import { useTranslations } from "next-intl";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface QuestionStat {
  id: number;
  question_text: string;
  attempt_count: number;
  accuracy_rate: number;
}

interface QuestionDataTableProps {
  title: string;
  data: QuestionStat[];
}

export function QuestionDataTable({ title, data }: QuestionDataTableProps) {
  const t = useTranslations("Admin.AdminStatistics");
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[60%]">{t("question")}</TableHead>
              <TableHead className="text-center">{t("attemptCount")}</TableHead>
              <TableHead className="text-center">{t("accuracyRate")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((q) => (
              <TableRow key={q.id}>
                <TableCell className="font-medium truncate max-w-sm">
                  {q.question_text}
                </TableCell>
                <TableCell className="text-center">{q.attempt_count}</TableCell>
                <TableCell className="text-center">
                  {q.accuracy_rate?.toFixed(1)}%
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
