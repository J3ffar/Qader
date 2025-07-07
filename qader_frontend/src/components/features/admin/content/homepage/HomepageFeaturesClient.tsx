"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { toast } from "sonner";
import { MoreHorizontal, PlusCircle } from "lucide-react";
import { useTranslations } from "next-intl";

import { queryKeys } from "@/constants/queryKeys";
import {
  createHomepageFeature,
  deleteHomepageFeature,
  getHomepageFeatures,
  updateHomepageFeature,
} from "@/services/api/admin/content.service";
import type { HomepageFeatureCard } from "@/types/api/admin/content.types";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
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
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import ConfirmationDialog from "@/components/shared/ConfirmationDialog";

const getFeatureSchema = (t: (key: string) => string) =>
  z.object({
    title: z.string().min(3, t("form.titleRequired")),
    text: z.string().min(10, t("form.textRequired")),
    icon_class: z.string().optional().nullable(),
    order: z.coerce.number().int().min(0),
    is_active: z.boolean(),
  });
type FeatureFormValues = z.infer<ReturnType<typeof getFeatureSchema>>;

export function HomepageFeaturesClient() {
  const t = useTranslations("Admin.Content.homepage.features");
  const queryClient = useQueryClient();
  const [isDialogOpen, setDialogOpen] = useState(false);
  const [selectedFeature, setSelectedFeature] =
    useState<HomepageFeatureCard | null>(null);

  const featureSchema = getFeatureSchema(t);

  const {
    data: response,
    isLoading,
    isError,
  } = useQuery({
    queryKey: queryKeys.admin.content.homepage.features(),
    queryFn: getHomepageFeatures,
  });
  const features = response?.results ?? [];

  const form = useForm<FeatureFormValues>({
    resolver: zodResolver(featureSchema),
    defaultValues: {
      title: "",
      text: "",
      icon_class: "",
      order: 0,
      is_active: true,
    },
  });

  const createMutation = useMutation({
    mutationFn: createHomepageFeature,
    onSuccess: () => {
      toast.success(t("toast.createSuccess"));
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.content.homepage.features(),
      });
      setDialogOpen(false);
    },
    onError: (err) => {
      toast.error(t("toast.createError"), { description: err.message });
    },
  });

  const updateMutation = useMutation({
    mutationFn: updateHomepageFeature,
    onSuccess: () => {
      toast.success(t("toast.updateSuccess"));
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.content.homepage.features(),
      });
      setDialogOpen(false);
    },
    onError: (err) => {
      toast.error(t("toast.updateError", { description: err.message }));
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteHomepageFeature,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.content.homepage.features(),
      });
      toast.success(t("toast.deleteSuccess"));
    },
    onMutate: async (idToDelete) => {
      await queryClient.cancelQueries({
        queryKey: queryKeys.admin.content.homepage.features(),
      });
      const previousFeatures = queryClient.getQueryData<any>(
        queryKeys.admin.content.homepage.features()
      );
      queryClient.setQueryData(
        queryKeys.admin.content.homepage.features(),
        (old: any) => ({
          ...old,
          results: old.results.filter(
            (f: HomepageFeatureCard) => f.id !== idToDelete
          ),
        })
      );
      return { previousFeatures };
    },
    onError: (err, _vars, context) => {
      queryClient.setQueryData(
        queryKeys.admin.content.homepage.features(),
        context?.previousFeatures
      );
      toast.error("Failed to delete feature.", { description: err.message });
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.content.homepage.features(),
      });
    },
  });

  const handleOpenDialog = (feature: HomepageFeatureCard | null = null) => {
    setSelectedFeature(feature);
    if (feature) {
      form.reset({
        title: feature.title,
        text: feature.text,
        icon_class: feature.icon_class,
        order: feature.order,
        is_active: feature.is_active,
      });
    } else {
      form.reset({
        title: "",
        text: "",
        icon_class: "",
        order: features.length,
        is_active: true,
      });
    }
    setDialogOpen(true);
  };

  const onSubmit = (values: FeatureFormValues) => {
    if (selectedFeature) {
      updateMutation.mutate({ id: selectedFeature.id, payload: values });
    } else {
      createMutation.mutate(values as any);
    }
  };

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle>{t("cardTitle")}</CardTitle>
              <CardDescription>{t("cardDescription")}</CardDescription>
            </div>
            <Button onClick={() => handleOpenDialog()}>
              <PlusCircle className="ltr:mr-2 rtl:ml-2 h-4 w-4" /> {t("addNew")}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="border rounded-md">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("table.order")}</TableHead>
                  <TableHead>{t("table.title")}</TableHead>
                  <TableHead className="hidden md:table-cell">
                    {t("table.text")}
                  </TableHead>
                  <TableHead>{t("table.status")}</TableHead>
                  <TableHead>
                    <span className="sr-only">{t("table.actions")}</span>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  Array.from({ length: 3 }).map((_, i) => (
                    <TableRow key={`skeleton-${i}`}>
                      <TableCell>
                        <Skeleton className="h-4 w-10" />
                      </TableCell>
                      <TableCell>
                        <Skeleton className="h-4 w-32" />
                      </TableCell>
                      <TableCell className="hidden md:table-cell">
                        <Skeleton className="h-4 w-full" />
                      </TableCell>
                      <TableCell>
                        <Skeleton className="h-6 w-16" />
                      </TableCell>
                      <TableCell>
                        <Skeleton className="h-8 w-8" />
                      </TableCell>
                    </TableRow>
                  ))
                ) : isError ? (
                  <TableRow>
                    <TableCell
                      colSpan={5}
                      className="text-center text-destructive"
                    >
                      Failed to load features.
                    </TableCell>
                  </TableRow>
                ) : (
                  features.map((feature) => (
                    <TableRow key={feature.id}>
                      <TableCell>{feature.order}</TableCell>
                      <TableCell className="font-medium">
                        {feature.title}
                      </TableCell>
                      <TableCell className="hidden md:table-cell text-sm text-muted-foreground">
                        {feature.text.substring(0, 70)}...
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={feature.is_active ? "default" : "secondary"}
                        >
                          {feature.is_active
                            ? t("statusLabels.active")
                            : t("statusLabels.inactive")}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <DropdownMenu modal={false}>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="h-8 w-8 p-0">
                              <span className="sr-only">
                                {t("actionsMenu.label")}
                              </span>
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuLabel>
                              {t("actionsMenu.label")}
                            </DropdownMenuLabel>
                            <DropdownMenuItem
                              onClick={() => handleOpenDialog(feature)}
                            >
                              {t("actionsMenu.edit")}
                            </DropdownMenuItem>
                            <ConfirmationDialog
                              triggerButton={
                                <DropdownMenuItem
                                  className="text-destructive"
                                  onSelect={(e) => e.preventDefault()}
                                >
                                  {t("actionsMenu.delete")}
                                </DropdownMenuItem>
                              }
                              title={t("deleteDialog.title")}
                              description={t("deleteDialog.description", {
                                title: feature.title,
                              })}
                              onConfirm={() =>
                                deleteMutation.mutate(feature.id)
                              }
                              isConfirming={
                                deleteMutation.isPending &&
                                selectedFeature?.id === feature.id
                              }
                            />
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
      <Dialog open={isDialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>
              {selectedFeature
                ? t("formDialog.editTitle")
                : t("formDialog.newTitle")}
            </DialogTitle>
          </DialogHeader>
          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(onSubmit)}
              className="space-y-4 py-4"
            >
              <FormField
                name="title"
                control={form.control}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("form.titleLabel")}</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                name="text"
                control={form.control}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("form.textLabel")}</FormLabel>
                    <FormControl>
                      <Textarea {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                name="icon_class"
                control={form.control}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("form.iconLabel")}</FormLabel>
                    <FormControl>
                      <Input {...field} value={field.value ?? ""} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                name="order"
                control={form.control}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("form.orderLabel")}</FormLabel>
                    <FormControl>
                      <Input type="number" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                name="is_active"
                control={form.control}
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3">
                    <FormLabel>{t("form.activeLabel")}</FormLabel>
                    <FormControl>
                      <Switch
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />
              <DialogFooter>
                <Button
                  type="submit"
                  disabled={
                    createMutation.isPending || updateMutation.isPending
                  }
                >
                  {t("form.saveButton")}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
    </>
  );
}
