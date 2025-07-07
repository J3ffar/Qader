"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getPageBySlug,
  updatePage,
} from "@/services/api/admin/content.service";
import { queryKeys } from "@/constants/queryKeys";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import * as z from "zod";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect } from "react";

import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { PATHS } from "@/constants/paths";
import {
  type Page,
  type StructuredContentValue,
} from "@/types/api/admin/content.types";
import { ImageUploader } from "./ImageUploader";
import { RepeaterField } from "./RepeaterField";
import { RichTextEditor } from "./RichTextEditor";

interface PageEditorProps {
  pageSlug: string;
  pageTitle: string;
}

const createPageSchema = (t: (key: string) => string, pageData?: Page) => {
  let structuredSchemaFields: Record<
    string,
    z.ZodObject<{ value: z.ZodTypeAny }>
  > = {};

  if (pageData?.content_structured) {
    structuredSchemaFields = Object.entries(pageData.content_structured).reduce(
      (acc, [key, data]) => {
        let fieldSchema;
        switch (data.type) {
          case "image":
          case "url":
          case "text":
            fieldSchema = z.string().nullable().optional();
            break;
          case "textarea":
          case "html":
            fieldSchema = z.string().nullable().optional();
            break;
          case "repeater":
            fieldSchema = z.array(z.any()).nullable().optional();
            break;
          default:
            fieldSchema = z.string().nullable().optional();
        }
        acc[key] = z.object({ value: fieldSchema });
        return acc;
      },
      {} as Record<string, z.ZodObject<{ value: z.ZodTypeAny }>>
    );
  }

  const structuredSchema = z.object(structuredSchemaFields);

  return z.object({
    title: z.string().min(3, t("titleMinLengthError")),
    is_published: z.boolean(),
    content: z.string().optional().nullable(),
    content_structured: structuredSchema.nullable(),
  });
};

export function PageEditor({ pageSlug, pageTitle }: PageEditorProps) {
  const queryClient = useQueryClient();
  const t = useTranslations("Admin.Content");

  const {
    data: page,
    isLoading,
    isError,
  } = useQuery({
    queryKey: queryKeys.admin.content.pages.detail(pageSlug),
    queryFn: () => getPageBySlug(pageSlug),
    enabled: !!pageSlug,
  });

  const PageSchema = createPageSchema(t, page);
  type PageFormValues = z.infer<typeof PageSchema>;

  const form = useForm<PageFormValues>({
    resolver: zodResolver(PageSchema),
    defaultValues: {
      title: "",
      is_published: false,
      content: "",
      content_structured: null,
    },
  });

  useEffect(() => {
    if (page) {
      const resetValues = {
        title: page.title ?? "",
        is_published: page.is_published ?? false,
        content: page.content ?? "",
        content_structured: page.content_structured
          ? Object.entries(page.content_structured).reduce(
              (acc, [key, val]) => {
                acc[key] = { value: val.value };
                return acc;
              },
              {} as Record<string, { value: any }>
            )
          : null,
      };
      form.reset(resetValues);
    }
  }, [page, form.reset]);

  const updateMutation = useMutation({
    mutationFn: (payload: any) => updatePage({ slug: pageSlug, payload }),
    onSuccess: (data) => {
      const params = { ordering: "id" };
      toast.success(t("pageUpdateSuccess"));
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.content.pages.detail(pageSlug),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.content.pages.list(params),
      });
      form.reset(form.getValues());
    },
    onError: (error) => {
      toast.error(t("pageUpdateError"), { description: error.message });
    },
  });

  function onSubmit(data: PageFormValues) {
    const originalStructuredContent = page?.content_structured;
    let reconstructedStructuredContent = null;
    if (originalStructuredContent && data.content_structured) {
      reconstructedStructuredContent = Object.keys(
        originalStructuredContent
      ).reduce((acc, key) => {
        const originalField = originalStructuredContent[key];
        const updatedValue = (data.content_structured as any)[key]?.value;

        acc[key] = {
          admin_title: originalField.admin_title,
          type: originalField.type,
          value: updatedValue,
        };
        return acc;
      }, {} as Record<string, { admin_title: string; type: string; value: any }>);
    }

    const payload = {
      title: data.title,
      is_published: data.is_published,
      ...(data.content !== undefined && { content: data.content }),
      ...(reconstructedStructuredContent && {
        content_structured: reconstructedStructuredContent,
      }),
    };
    updateMutation.mutate(payload);
  }

  const renderFormField = (key: string, fieldData: StructuredContentValue) => {
    const fieldName = `content_structured.${key}.value` as any;

    switch (fieldData.type) {
      case "text":
      case "url":
        return (
          <FormField
            control={form.control}
            name={fieldName}
            render={({ field }) => (
              <FormItem>
                <FormLabel>{fieldData.admin_title}</FormLabel>
                <FormControl>
                  <Input
                    placeholder={t("enterPlaceholder", {
                      field: fieldData.admin_title.toLowerCase(),
                    })}
                    {...field}
                    value={field.value ?? ""}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        );
      case "textarea":
      case "html":
        return (
          <FormField
            control={form.control}
            name={fieldName}
            render={({ field }) => (
              <FormItem>
                <FormLabel>{fieldData.admin_title}</FormLabel>
                <FormControl>
                  <Textarea
                    rows={5}
                    placeholder={t("enterPlaceholder", {
                      field: fieldData.admin_title.toLowerCase(),
                    })}
                    {...field}
                    value={field.value ?? ""}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        );
      case "image":
        return (
          <FormField
            control={form.control}
            name={fieldName}
            render={({ field }) => (
              <FormItem>
                <FormLabel>{fieldData.admin_title}</FormLabel>
                <FormControl>
                  <ImageUploader
                    pageSlug={pageSlug}
                    allPageImages={page?.images ?? []}
                    value={field.value}
                    onChange={field.onChange}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        );
      case "repeater":
        return (
          <RepeaterField
            form={form}
            name={fieldName}
            label={fieldData.admin_title}
            initialData={fieldData.value}
          />
        );
      default:
        return (
          <div className="text-sm text-destructive">
            {t("unsupportedField", { type: fieldData.type })}
          </div>
        );
    }
  };

  if (isLoading) {
    return <PageEditorSkeleton />;
  }

  if (isError) {
    return (
      <div className="text-center py-10 text-destructive">
        {t("loadingError")}
      </div>
    );
  }

  return (
    <>
      <Breadcrumb className="mb-4">
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink href={PATHS.ADMIN.DASHBOARD}>
              {t("breadcrumbDashboard")}
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbLink href={PATHS.ADMIN.CONTENT_PAGES_LIST}>
              {t("breadcrumbContent")}
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>{pageTitle}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
            <div className="lg:col-span-2 space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>{t("pageDetails")}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <FormField
                    control={form.control}
                    name="title"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>{t("pageTitleLabel")}</FormLabel>
                        <FormControl>
                          <Input {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </CardContent>
              </Card>

              {page?.content_structured && (
                <Card>
                  <CardHeader>
                    <CardTitle>{t("structuredContent")}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {Object.entries(page.content_structured).map(
                      ([key, fieldData]) => (
                        <div key={key}>{renderFormField(key, fieldData)}</div>
                      )
                    )}
                  </CardContent>
                </Card>
              )}

              {page?.content !== null && (
                <Card>
                  <CardHeader>
                    <CardTitle>{t("legacyContent")}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <FormField
                      control={form.control}
                      name="content"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>{t("htmlContentLabel")}</FormLabel>
                          <FormControl>
                            <RichTextEditor
                              value={field.value ?? ""}
                              onChange={field.onChange}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </CardContent>
                </Card>
              )}
            </div>

            <div className="lg:col-span-1 space-y-6 sticky top-24">
              <Card>
                <CardHeader>
                  <CardTitle>{t("publishing")}</CardTitle>
                </CardHeader>
                <CardContent>
                  <FormField
                    control={form.control}
                    name="is_published"
                    render={({ field }) => (
                      <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                        <div className="space-y-0.5">
                          <FormLabel>{t("publishPageLabel")}</FormLabel>
                        </div>
                        <FormControl>
                          <Switch
                            checked={field.value}
                            onCheckedChange={field.onChange}
                          />
                        </FormControl>
                      </FormItem>
                    )}
                  />
                </CardContent>
                <CardFooter className="flex justify-end">
                  <Button
                    type="submit"
                    disabled={
                      updateMutation.isPending || !form.formState.isDirty
                    }
                  >
                    {updateMutation.isPending && (
                      <Loader2 className="ltr:mr-2 rtl:ml-2 h-4 w-4 animate-spin" />
                    )}
                    {updateMutation.isPending ? t("saving") : t("saveChanges")}
                  </Button>
                </CardFooter>
              </Card>
            </div>
          </div>
        </form>
      </Form>
    </>
  );
}

const PageEditorSkeleton = () => (
  <div className="space-y-4">
    <Skeleton className="h-6 w-1/2" />
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
      <div className="lg:col-span-2 space-y-6">
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-1/4" />
          </CardHeader>
          <CardContent className="space-y-4">
            <Skeleton className="h-10 w-full" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-1/4" />
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Skeleton className="h-4 w-1/5" />
              <Skeleton className="h-20 w-full" />
            </div>
            <div className="space-y-2">
              <Skeleton className="h-4 w-1/5" />
              <Skeleton className="h-20 w-full" />
            </div>
            <div className="space-y-2">
              <Skeleton className="h-4 w-1/5" />
              <Skeleton className="h-20 w-full" />
            </div>
          </CardContent>
        </Card>
      </div>
      <div className="lg:col-span-1 space-y-6">
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-1/3" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-12 w-full" />
          </CardContent>
          <CardFooter className="flex justify-end">
            <Skeleton className="h-10 w-24" />
          </CardFooter>
        </Card>
      </div>
    </div>
  </div>
);
