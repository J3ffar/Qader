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
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

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
import { ImageUploader } from "./ImageUploader"; // Correctly imported now
import { RepeaterField } from "./RepeaterField";

interface PageEditorProps {
  pageSlug: string;
  pageTitle: string;
}

// Dynamically build the Zod schema based on the page data
const createPageSchema = (pageData?: Page) => {
  let structuredSchemaFields: Record<
    string,
    z.ZodObject<{ value: z.ZodTypeAny }>
  > = {};

  if (pageData?.content_structured) {
    // FIX 1: TIGHTEN THE SCHEMA. Replace z.any() with specific types.
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
            fieldSchema = z.array(z.any()).nullable().optional(); // Repeater can stay as z.any() for now
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
    title: z.string().min(3, "Title must be at least 3 characters."),
    is_published: z.boolean(),
    content: z.string().optional().nullable(),
    content_structured: structuredSchema.nullable(),
  });
};

export function PageEditor({ pageSlug, pageTitle }: PageEditorProps) {
  const queryClient = useQueryClient();

  const {
    data: page,
    isLoading,
    isError,
  } = useQuery({
    queryKey: queryKeys.admin.content.pages.detail(pageSlug),
    queryFn: () => getPageBySlug(pageSlug),
    enabled: !!pageSlug,
  });

  const PageSchema = createPageSchema(page);
  type PageFormValues = z.infer<typeof PageSchema>;

  const form = useForm<PageFormValues>({
    resolver: zodResolver(PageSchema),
    values: {
      title: page?.title ?? "",
      is_published: page?.is_published ?? false,
      content: page?.content ?? "",
      content_structured: page?.content_structured
        ? Object.entries(page.content_structured).reduce((acc, [key, val]) => {
            // FIX 2: EXPLICITLY TYPE THE ACCUMULATOR
            acc[key] = { value: val.value };
            return acc;
          }, {} as Record<string, { value: any }>)
        : null,
    },
  });

  // ... (updateMutation logic is the same)
  const updateMutation = useMutation({
    mutationFn: (payload: any) => updatePage({ slug: pageSlug, payload }),
    onSuccess: (data) => {
      toast.success("Page updated successfully!");
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.content.pages.detail(pageSlug),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.content.pages.list(),
      });
      form.reset(form.getValues());
    },
    onError: (error) => {
      toast.error("Failed to update page.", { description: error.message });
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
        // The type of data.content_structured is now properly inferred thanks to the schema fix
        const updatedValue = (data.content_structured as any)[key]?.value;

        acc[key] = {
          admin_title: originalField.admin_title,
          type: originalField.type,
          value: updatedValue,
        };
        // FIX 2 (continued): EXPLICITLY TYPE THE ACCUMULATOR
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
    // FIX 3: USE TYPE ASSERTION FOR THE DYNAMIC `name` PROP
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
                    placeholder={`Enter ${fieldData.admin_title.toLowerCase()}`}
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
                    placeholder={`Enter ${fieldData.admin_title.toLowerCase()}`}
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
          // Use our new dedicated component for repeaters
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
            Unsupported field type: {fieldData.type}
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
        Error loading page data. Please try again.
      </div>
    );
  }

  return (
    <>
      <Breadcrumb className="mb-4">
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink href={PATHS.ADMIN.DASHBOARD}>
              Dashboard
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbLink href={PATHS.ADMIN.CONTENT_PAGES_LIST}>
              Content
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
                  <CardTitle>Page Details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <FormField
                    control={form.control}
                    name="title"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Page Title</FormLabel>
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
                    <CardTitle>Structured Content</CardTitle>
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
                    <CardTitle>Simple Content (Legacy)</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <FormField
                      control={form.control}
                      name="content"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>HTML Content</FormLabel>
                          <FormControl>
                            <Textarea
                              rows={15}
                              {...field}
                              value={field.value ?? ""}
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
                  <CardTitle>Publishing</CardTitle>
                </CardHeader>
                <CardContent>
                  <FormField
                    control={form.control}
                    name="is_published"
                    render={({ field }) => (
                      <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                        <div className="space-y-0.5">
                          <FormLabel>Publish Page</FormLabel>
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
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    )}
                    {updateMutation.isPending ? "Saving..." : "Save Changes"}
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
