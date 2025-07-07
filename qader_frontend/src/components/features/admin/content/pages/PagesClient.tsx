"use client";

import { useQuery } from "@tanstack/react-query";
import { getPages } from "@/services/api/admin/content.service";
import { queryKeys } from "@/constants/queryKeys";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Edit } from "lucide-react";
import { PATHS } from "@/constants/paths";
import { Badge } from "@/components/ui/badge";
import { useTranslations } from "next-intl";

export function PagesClient() {
  const t = useTranslations("Admin.Content"); // Assuming you have i18n setup

  // The API returns a paginated object, so let's name the data appropriately.
  const { data: paginatedResponse, isLoading } = useQuery({
    queryKey: queryKeys.admin.content.pages.list(),
    queryFn: getPages,
  });

  // Now, we get the array of pages from the 'results' key.
  const pages = paginatedResponse?.results;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("allPagesTitle")}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="border rounded-md">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("table.title")}</TableHead>
                <TableHead>{t("table.slug")}</TableHead>
                <TableHead>{t("table.status")}</TableHead>
                <TableHead className="text-right">
                  {t("table.actions")}
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading &&
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell>
                      <Skeleton className="h-5 w-48" />
                    </TableCell>
                    <TableCell>
                      <Skeleton className="h-5 w-32" />
                    </TableCell>
                    <TableCell>
                      <Skeleton className="h-5 w-20" />
                    </TableCell>
                    <TableCell className="text-right">
                      <Skeleton className="h-8 w-8 ml-auto" />
                    </TableCell>
                  </TableRow>
                ))}

              {/* THIS IS THE FIX: We are now mapping over `pages` which is the .results array */}
              {!isLoading &&
                pages?.map((page) => (
                  <TableRow key={page.id}>
                    <TableCell className="font-medium">{page.title}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {page.slug}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={page.is_published ? "default" : "secondary"}
                      >
                        {page.is_published
                          ? t("status.published")
                          : t("status.draft")}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button asChild variant="ghost" size="icon">
                        <Link href={PATHS.ADMIN.CONTENT_PAGE_EDIT(page.slug)}>
                          <Edit className="h-4 w-4" />
                          <span className="sr-only">{t("editPage")}</span>
                        </Link>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}

              {!isLoading && pages?.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} className="h-24 text-center">
                    {t("noPagesFound")}
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
        {/* We can add pagination controls here later if needed */}
      </CardContent>
    </Card>
  );
}
