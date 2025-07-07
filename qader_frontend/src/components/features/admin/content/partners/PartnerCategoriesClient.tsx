"use client";

import { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { toast } from "sonner";
import { MoreHorizontal, PlusCircle, Image as ImageIcon } from "lucide-react";
import { useTranslations } from "next-intl";

import { queryKeys } from "@/constants/queryKeys";
import {
  createPartnerCategory,
  deletePartnerCategory,
  getPartnerCategories,
  updatePartnerCategory,
} from "@/services/api/admin/content.service";
import type {
  PartnerCategory,
  PartnerCategoryPayload,
} from "@/types/api/admin/content.types";

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
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

const MAX_DESCRIPTION_LENGTH = 70;

// Zod schema is now a function to accept the translation function 't'
const getCategorySchema = (t: (key: string) => string) =>
  z.object({
    name: z.string().min(3, t("form.nameRequired")),
    description: z.string().min(10, t("form.descriptionRequired")),
    google_form_link: z.string().url(t("form.linkInvalid")),
    order: z.coerce.number().int().min(0),
    is_active: z.boolean(),
  });

type CategoryFormValues = z.infer<ReturnType<typeof getCategorySchema>>;

export function PartnerCategoriesClient() {
  const t = useTranslations("Admin.Content.partners");
  const queryClient = useQueryClient();
  const [isDialogOpen, setDialogOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] =
    useState<PartnerCategory | null>(null);
  const iconFileRef = useRef<HTMLInputElement>(null);

  const categorySchema = getCategorySchema(t);

  const { data: response, isLoading } = useQuery({
    queryKey: queryKeys.admin.content.partners.categories(),
    queryFn: getPartnerCategories,
  });
  const categories = response?.results ?? [];

  const form = useForm<CategoryFormValues>({
    resolver: zodResolver(categorySchema),
    defaultValues: {
      name: "",
      description: "",
      google_form_link: "",
      order: 0,
      is_active: true,
    },
  });

  const createMutation = useMutation({
    mutationFn: createPartnerCategory,
    onSuccess: () => {
      toast.success(t("toast.createSuccess"));
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.content.partners.categories(),
      });
      setDialogOpen(false);
    },
    onError: (err) =>
      toast.error(t("toast.createError"), { description: err.message }),
  });

  const updateMutation = useMutation({
    mutationFn: updatePartnerCategory,
    onSuccess: () => {
      toast.success(t("toast.updateSuccess"));
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.content.partners.categories(),
      });
      setDialogOpen(false);
    },
    onError: (err) =>
      toast.error(t("toast.updateError"), { description: err.message }),
  });

  const deleteMutation = useMutation({
    mutationFn: deletePartnerCategory,
    onSuccess: () => toast.success(t("toast.deleteSuccess")),
    onMutate: async (idToDelete) => {
      await queryClient.cancelQueries({
        queryKey: queryKeys.admin.content.partners.categories(),
      });
      const previousData = queryClient.getQueryData<any>(
        queryKeys.admin.content.partners.categories()
      );
      queryClient.setQueryData(
        queryKeys.admin.content.partners.categories(),
        (old: any) => ({
          ...old,
          results: old.results.filter(
            (c: PartnerCategory) => c.id !== idToDelete
          ),
        })
      );
      return { previousData };
    },
    onError: (err, _vars, context) => {
      queryClient.setQueryData(
        queryKeys.admin.content.partners.categories(),
        context?.previousData
      );
      toast.error(t("toast.deleteError"), { description: err.message });
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.content.partners.categories(),
      });
    },
  });

  const handleOpenDialog = (category: PartnerCategory | null = null) => {
    setSelectedCategory(category);
    if (category) {
      form.reset(category);
    } else {
      form.reset({
        name: "",
        description: "",
        google_form_link: "",
        order: categories.length,
        is_active: true,
      });
    }
    setDialogOpen(true);
  };

  const onSubmit = (values: CategoryFormValues) => {
    const iconFile = iconFileRef.current?.files?.[0];
    const payload: PartnerCategoryPayload = {
      ...values,
      ...(iconFile && { icon_image: iconFile }),
    };

    if (selectedCategory) {
      updateMutation.mutate({ id: selectedCategory.id, payload });
    } else {
      createMutation.mutate(payload);
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
              <PlusCircle className="ltr:mr-2 rtl:ml-2 h-4 w-4" />{" "}
              {t("addNewCategory")}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="border rounded-md">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("table.icon")}</TableHead>
                  <TableHead>{t("table.name")}</TableHead>
                  <TableHead className="hidden md:table-cell">
                    {t("table.description")}
                  </TableHead>
                  <TableHead>{t("table.status")}</TableHead>
                  <TableHead>
                    <span className="sr-only">{t("table.actions")}</span>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading &&
                  Array.from({ length: 3 }).map((_, i) => (
                    <TableRow key={i}>
                      <TableCell>
                        <Skeleton className="h-10 w-10 rounded-full" />
                      </TableCell>
                      <TableCell>
                        <Skeleton className="h-5 w-32" />
                      </TableCell>
                      <TableCell className="hidden md:table-cell">
                        <Skeleton className="h-5 w-full" />
                      </TableCell>
                      <TableCell>
                        <Skeleton className="h-6 w-16" />
                      </TableCell>
                      <TableCell>
                        <Skeleton className="h-8 w-8" />
                      </TableCell>
                    </TableRow>
                  ))}
                {categories.map((category) => (
                  <TableRow key={category.id}>
                    <TableCell>
                      <Avatar>
                        <AvatarImage
                          src={category.icon_image ?? undefined}
                          alt={category.name}
                        />
                        <AvatarFallback>
                          <ImageIcon className="h-5 w-5 text-muted-foreground" />
                        </AvatarFallback>
                      </Avatar>
                    </TableCell>
                    <TableCell className="font-medium">
                      {category.name}
                    </TableCell>
                    <TableCell className="hidden md:table-cell text-sm text-muted-foreground">
                      {category.description.length > MAX_DESCRIPTION_LENGTH
                        ? `${category.description.substring(
                            0,
                            MAX_DESCRIPTION_LENGTH
                          )}...`
                        : category.description}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={category.is_active ? "default" : "secondary"}
                      >
                        {category.is_active
                          ? t("statusLabels.active")
                          : t("statusLabels.inactive")}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <DropdownMenu modal={false}>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" className="h-8 w-8 p-0">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuLabel>
                            {t("actionsMenu.label")}
                          </DropdownMenuLabel>
                          <DropdownMenuItem
                            onClick={() => handleOpenDialog(category)}
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
                name="description"
                control={form.control}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("form.descriptionLabel")}</FormLabel>
                    <FormControl>
                      <Textarea {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormItem>
                <FormLabel>{t("form.iconLabel")}</FormLabel>
                <FormControl>
                  <Input
                    type="file"
                    ref={iconFileRef}
                    accept="image/png, image/jpeg, image/svg+xml"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
              <FormField
                name="google_form_link"
                control={form.control}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("form.linkLabel")}</FormLabel>
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
                  <FormItem className="flex items-center justify-between rounded-lg border p-3">
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
