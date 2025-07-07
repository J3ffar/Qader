"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { toast } from "sonner";
import { MoreHorizontal, PlusCircle, ListChecks } from "lucide-react";
import { useTranslations } from "next-intl";

import { queryKeys } from "@/constants/queryKeys";
import {
  createFaqCategory,
  deleteFaqCategory,
  getFaqCategories,
  updateFaqCategory,
} from "@/services/api/admin/content.service";
import type { FaqCategory } from "@/types/api/admin/content.types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
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
import ConfirmationDialog from "@/components/shared/ConfirmationDialog";

const getCategorySchema = (t: (key: string) => string) =>
  z.object({
    name: z.string().min(3, t("form.nameRequired")),
    order: z.coerce.number().int().min(0),
  });
type CategoryFormValues = z.infer<ReturnType<typeof getCategorySchema>>;

interface FaqCategoriesClientProps {
  onManageItems: (category: FaqCategory) => void;
}

export function FaqCategoriesClient({
  onManageItems,
}: FaqCategoriesClientProps) {
  const t = useTranslations("Admin.Content.faqs.categories");
  const tShared = useTranslations("Admin.Content.faqs.shared");
  const queryClient = useQueryClient();
  const [isDialogOpen, setDialogOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<FaqCategory | null>(
    null
  );

  const categorySchema = getCategorySchema(t);

  const { data: response, isLoading } = useQuery({
    queryKey: queryKeys.admin.content.faqs.categoryList(),
    queryFn: getFaqCategories,
  });
  const categories = response?.results ?? [];

  const form = useForm<CategoryFormValues>({
    resolver: zodResolver(categorySchema),
    defaultValues: { name: "", order: 0 },
  });

  const createMutation = useMutation({
    mutationFn: createFaqCategory,
    onSuccess: () => {
      toast.success(t("toast.createSuccess"));
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.content.faqs.categoryList(),
      });
      setDialogOpen(false);
    },
    onError: () => toast.error(t("toast.createError")),
  });

  const updateMutation = useMutation({
    mutationFn: updateFaqCategory,
    onSuccess: () => {
      toast.success(t("toast.updateSuccess"));
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.content.faqs.categoryList(),
      });
      setDialogOpen(false);
    },
    onError: () => toast.error(t("toast.updateError")),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteFaqCategory,
    onSuccess: () => toast.success(t("toast.deleteSuccess")),
    onMutate: async (idToDelete) => {
      await queryClient.cancelQueries({
        queryKey: queryKeys.admin.content.faqs.categoryList(),
      });
      const previousData = queryClient.getQueryData<any>(
        queryKeys.admin.content.faqs.categoryList()
      );
      queryClient.setQueryData(
        queryKeys.admin.content.faqs.categoryList(),
        (old: any) => ({
          ...old,
          results: old.results.filter((c: FaqCategory) => c.id !== idToDelete),
        })
      );
      return { previousData };
    },
    onError: (_err, _vars, context) => {
      queryClient.setQueryData(
        queryKeys.admin.content.faqs.categoryList(),
        context?.previousData
      );
      toast.error(t("toast.deleteError"));
    },
    onSettled: () =>
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.content.faqs.categoryList(),
      }),
  });

  const handleOpenDialog = (category: FaqCategory | null = null) => {
    setSelectedCategory(category);
    form.reset(category ?? { name: "", order: categories.length });
    setDialogOpen(true);
  };

  const onSubmit = (values: CategoryFormValues) => {
    if (selectedCategory) {
      updateMutation.mutate({ id: selectedCategory.id, payload: values });
    } else {
      createMutation.mutate(values as any);
    }
  };

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <CardTitle>{t("cardTitle")}</CardTitle>
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
                  <TableHead>{t("table.name")}</TableHead>
                  <TableHead className="text-right">
                    {t("table.actions")}
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading &&
                  Array.from({ length: 3 }).map((_, i) => (
                    <TableRow key={i}>
                      <TableCell>
                        <Skeleton className="h-5 w-8" />
                      </TableCell>
                      <TableCell>
                        <Skeleton className="h-5 w-48" />
                      </TableCell>
                      <TableCell className="text-right">
                        <Skeleton className="h-8 w-48 ml-auto" />
                      </TableCell>
                    </TableRow>
                  ))}
                {categories.map((category) => (
                  <TableRow key={category.id}>
                    <TableCell>{category.order}</TableCell>
                    <TableCell className="font-medium w-full">
                      {category.name}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onManageItems(category)}
                        className="ltr:mr-2 rtl:ml-2"
                      >
                        <ListChecks className="h-4 w-4 ltr:mr-2 rtl:ml-2" />{" "}
                        {t("manageItemsButton")}
                      </Button>
                      <DropdownMenu modal={false}>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" className="h-8 w-8 p-0">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            onClick={() => handleOpenDialog(category)}
                          >
                            {tShared("actionsMenu.edit")}
                          </DropdownMenuItem>
                          <ConfirmationDialog
                            triggerButton={
                              <DropdownMenuItem
                                className="text-destructive"
                                onSelect={(e) => e.preventDefault()}
                              >
                                {tShared("actionsMenu.delete")}
                              </DropdownMenuItem>
                            }
                            title={t("deleteDialog.title")}
                            description={t("deleteDialog.description", {
                              name: category.name,
                            })}
                            onConfirm={() => deleteMutation.mutate(category.id)}
                            isConfirming={
                              deleteMutation.isPending &&
                              selectedCategory?.id === category.id
                            }
                          />
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
      <Dialog open={isDialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>
              {selectedCategory
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
                name="name"
                control={form.control}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("form.nameLabel")}</FormLabel>
                    <FormControl>
                      <Input {...field} />
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
                    <FormLabel>{tShared("form.orderLabel")}</FormLabel>
                    <FormControl>
                      <Input type="number" {...field} />
                    </FormControl>
                    <FormMessage />
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
                  {tShared("form.saveButton")}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
    </>
  );
}
