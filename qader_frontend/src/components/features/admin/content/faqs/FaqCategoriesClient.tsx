"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { toast } from "sonner";
import { MoreHorizontal, PlusCircle, ListChecks } from "lucide-react";

import { queryKeys } from "@/constants/queryKeys";
import {
  createFaqCategory,
  deleteFaqCategory,
  getFaqCategories,
  updateFaqCategory,
} from "@/services/api/admin/content.service";
import type { FaqCategory } from "@/types/api/admin/content.types";
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

const categorySchema = z.object({
  name: z.string().min(3, "Name is required."),
  order: z.coerce.number().int().min(0),
});
type CategoryFormValues = z.infer<typeof categorySchema>;

interface FaqCategoriesClientProps {
  onManageItems: (category: FaqCategory) => void;
}

export function FaqCategoriesClient({
  onManageItems,
}: FaqCategoriesClientProps) {
  const queryClient = useQueryClient();
  const [isDialogOpen, setDialogOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<FaqCategory | null>(
    null
  );

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
      toast.success("Category created successfully!");
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.content.faqs.categoryList(),
      });
      setDialogOpen(false);
    },
    onError: (err) =>
      toast.error("Failed to create category.", { description: err.message }),
  });

  const updateMutation = useMutation({
    mutationFn: updateFaqCategory,
    onSuccess: () => {
      toast.success("Category updated successfully!");
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.content.faqs.categoryList(),
      });
      setDialogOpen(false);
    },
    onError: (err) =>
      toast.error("Failed to update category.", { description: err.message }),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteFaqCategory,
    onSuccess: () => toast.success("Category deleted."),
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
    onError: (err, _vars, context) => {
      queryClient.setQueryData(
        queryKeys.admin.content.faqs.categoryList(),
        context?.previousData
      );
      toast.error("Failed to delete category.", { description: err.message });
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
            <CardTitle>FAQ Categories</CardTitle>
            <Button onClick={() => handleOpenDialog()}>
              <PlusCircle className="ltr:mr-2 rtl:ml-2 h-4 w-4" /> Add New
              Category
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="border rounded-md">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Order</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
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
                        className="mr-2"
                      >
                        <ListChecks className="h-4 w-4 ltr:mr-2 rtl:ml-2" />{" "}
                        Manage Items
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
                            Edit
                          </DropdownMenuItem>
                          <ConfirmationDialog
                            triggerButton={
                              <DropdownMenuItem
                                className="text-destructive"
                                onSelect={(e) => e.preventDefault()}
                              >
                                Delete
                              </DropdownMenuItem>
                            }
                            title="Delete FAQ Category"
                            description={`Are you sure you want to delete the category "${category.name}"? This will also delete all questions inside it.`}
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
              {selectedCategory ? "Edit Category" : "New Category"}
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
                    <FormLabel>Name</FormLabel>
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
                    <FormLabel>Display Order</FormLabel>
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
                  Save
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
    </>
  );
}
