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
  createHomepageStat,
  deleteHomepageStat,
  getHomepageStats,
  updateHomepageStat,
} from "@/services/api/admin/content.service";
import type { HomepageStatistic } from "@/types/api/admin/content.types";
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
import { Switch } from "@/components/ui/switch";
import ConfirmationDialog from "@/components/shared/ConfirmationDialog";

const getStatSchema = (t: (key: string) => string) =>
  z.object({
    label: z.string().min(3, t("form.labelRequired")),
    value: z.string().min(1, t("form.valueRequired")),
    icon_class: z.string().optional().nullable(),
    order: z.coerce.number().int().min(0),
    is_active: z.boolean(),
  });
type StatFormValues = z.infer<ReturnType<typeof getStatSchema>>;

export function HomepageStatsClient() {
  const t = useTranslations("Admin.Content.homepage.stats");
  const tFeatures = useTranslations("Admin.Content.homepage.features"); // For shared keys like statusLabels
  const queryClient = useQueryClient();
  const [isDialogOpen, setDialogOpen] = useState(false);
  const [selectedStat, setSelectedStat] = useState<HomepageStatistic | null>(
    null
  );

  const statSchema = getStatSchema(t);

  const {
    data: response,
    isLoading,
    isError,
  } = useQuery({
    queryKey: queryKeys.admin.content.homepage.stats(),
    queryFn: getHomepageStats,
  });
  const stats = response?.results ?? [];

  const form = useForm<StatFormValues>({
    resolver: zodResolver(statSchema),
    defaultValues: {
      label: "",
      value: "",
      icon_class: "",
      order: 0,
      is_active: true,
    },
  });

  const createMutation = useMutation({
    mutationFn: createHomepageStat,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.content.homepage.stats(),
      });
      toast.success(t("toast.createSuccess"));
      setDialogOpen(false);
    },
    onError: () => {
      toast.error(t("toast.createError"));
    },
  });

  const updateMutation = useMutation({
    mutationFn: updateHomepageStat,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.content.homepage.stats(),
      });
      toast.success(t("toast.updateSuccess"));
      setDialogOpen(false);
    },
    onError: () => {
      toast.error(t("toast.updateError"));
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteHomepageStat,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.content.homepage.stats(),
      });
      toast.success(t("toast.deleteSuccess"));
    },
    onMutate: async (idToDelete) => {
      await queryClient.cancelQueries({
        queryKey: queryKeys.admin.content.homepage.stats(),
      });
      const previousStats = queryClient.getQueryData<any>(
        queryKeys.admin.content.homepage.stats()
      );
      queryClient.setQueryData(
        queryKeys.admin.content.homepage.stats(),
        (old: any) => ({
          ...old,
          results: old.results.filter(
            (s: HomepageStatistic) => s.id !== idToDelete
          ),
        })
      );
      return { previousStats };
    },
    onError: (err, _vars, context) => {
      queryClient.setQueryData(
        queryKeys.admin.content.homepage.stats(),
        context?.previousStats
      );
      toast.error("Failed to delete statistic.", { description: err.message });
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.content.homepage.stats(),
      });
    },
  });

  const handleOpenDialog = (stat: HomepageStatistic | null = null) => {
    setSelectedStat(stat);
    if (stat) {
      form.reset({
        label: stat.label,
        value: stat.value,
        icon_class: stat.icon_class,
        order: stat.order,
        is_active: stat.is_active,
      });
    } else {
      form.reset({
        label: "",
        value: "",
        icon_class: "",
        order: stats.length,
        is_active: true,
      });
    }
    setDialogOpen(true);
  };

  const onSubmit = (values: StatFormValues) => {
    if (selectedStat) {
      updateMutation.mutate({ id: selectedStat.id, payload: values });
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
                  <TableHead>{t("table.label")}</TableHead>
                  <TableHead>{t("table.value")}</TableHead>
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
                      <TableCell>
                        <Skeleton className="h-4 w-24" />
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
                      Failed to load stats.
                    </TableCell>
                  </TableRow>
                ) : (
                  stats.map((stat) => (
                    <TableRow key={stat.id}>
                      <TableCell>{stat.order}</TableCell>
                      <TableCell className="font-medium">
                        {stat.label}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {stat.value}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={stat.is_active ? "default" : "secondary"}
                        >
                          {stat.is_active
                            ? tFeatures("statusLabels.active")
                            : tFeatures("statusLabels.inactive")}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <DropdownMenu modal={false}>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="h-8 w-8 p-0">
                              <span className="sr-only">
                                {tFeatures("actionsMenu.label")}
                              </span>
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuLabel>
                              {tFeatures("actionsMenu.label")}
                            </DropdownMenuLabel>
                            <DropdownMenuItem
                              onClick={() => handleOpenDialog(stat)}
                            >
                              {tFeatures("actionsMenu.edit")}
                            </DropdownMenuItem>
                            <ConfirmationDialog
                              triggerButton={
                                <DropdownMenuItem
                                  className="text-destructive"
                                  onSelect={(e) => e.preventDefault()}
                                >
                                  {tFeatures("actionsMenu.delete")}
                                </DropdownMenuItem>
                              }
                              title={t("deleteDialog.title")}
                              description={t("deleteDialog.description", {
                                label: stat.label,
                              })}
                              onConfirm={() => deleteMutation.mutate(stat.id)}
                              isConfirming={
                                deleteMutation.isPending &&
                                selectedStat?.id === stat.id
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
              {selectedStat
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
                name="label"
                control={form.control}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("form.labelLabel")}</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                name="value"
                control={form.control}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("form.valueLabel")}</FormLabel>
                    <FormControl>
                      <Input {...field} />
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
