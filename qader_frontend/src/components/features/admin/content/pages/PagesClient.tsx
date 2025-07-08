"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Edit, Image as ImageIcon } from "lucide-react";
import { useTranslations } from "next-intl";

import { getPages } from "@/services/api/admin/content.service";
import { queryKeys } from "@/constants/queryKeys";
import { PATHS } from "@/constants/paths";
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
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

const MAX_IMAGES_TO_DISPLAY = 3;

export function PagesClient() {
  const t = useTranslations("Admin.Content");
  const params = { ordering: "id" };

  const { data: paginatedResponse, isLoading } = useQuery({
    queryKey: queryKeys.admin.content.pages.list(params),
    queryFn: () => getPages(params),
  });

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
                <TableHead>{t("table.images")}</TableHead>
                <TableHead>{t("table.slug")}</TableHead>
                <TableHead>{t("table.status")}</TableHead>
                <TableHead className="text-center">
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
                      <div className="flex items-center -space-x-2 rtl:space-x-reverse">
                        <Skeleton className="h-8 w-8 rounded-full" />
                        <Skeleton className="h-8 w-8 rounded-full" />
                      </div>
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

              {!isLoading &&
                pages?.map((page) => (
                  <TableRow key={page.id}>
                    <TableCell className="font-medium">{page.title}</TableCell>
                    <TableCell>
                      {/* NEW IMAGE DISPLAY LOGIC */}
                      {page.images && page.images.length > 0 ? (
                        <div className="flex items-center -space-x-2 rtl:space-x-reverse">
                          <TooltipProvider delayDuration={100}>
                            {page.images
                              .slice(0, MAX_IMAGES_TO_DISPLAY)
                              .map((image) => (
                                <Tooltip key={image.id}>
                                  <TooltipTrigger asChild>
                                    <Avatar className="border-2 border-background">
                                      <AvatarImage
                                        src={image.image_url}
                                        alt={image.alt_text}
                                      />
                                      <AvatarFallback>
                                        <ImageIcon className="h-4 w-4 text-muted-foreground" />
                                      </AvatarFallback>
                                    </Avatar>
                                  </TooltipTrigger>
                                  <TooltipContent>
                                    <p>{image.name}</p>
                                  </TooltipContent>
                                </Tooltip>
                              ))}
                            {page.images.length > MAX_IMAGES_TO_DISPLAY && (
                              <Avatar className="border-2 border-background">
                                <AvatarFallback>
                                  +{page.images.length - MAX_IMAGES_TO_DISPLAY}
                                </AvatarFallback>
                              </Avatar>
                            )}
                          </TooltipProvider>
                        </div>
                      ) : (
                        <span className="text-xs text-muted-foreground">
                          {t("noImages")}
                        </span>
                      )}
                    </TableCell>
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
                      <Button asChild variant="outline">
                        <Link href={PATHS.ADMIN.CONTENT_PAGE_EDIT(page.slug)}>
                          <Edit className="h-4 w-4" />
                          تعديل المحتوى
                          <span className="sr-only">{t("editPage")}</span>
                        </Link>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}

              {!isLoading && pages?.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="h-24 text-center">
                    {t("noPagesFound")}
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
