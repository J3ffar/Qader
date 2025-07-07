"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { toast } from "sonner";
import { MoreHorizontal, PlusCircle, ArrowLeft } from "lucide-react";

import { queryKeys } from "@/constants/queryKeys";
import {
  createFaqItem,
  deleteFaqItem,
  getFaqItems,
  updateFaqItem,
} from "@/services/api/admin/content.service";
import type { FaqCategory, FaqItem } from "@/types/api/admin/content.types";
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

const itemSchema = z.object({
  question: z.string().min(5, "Question is required."),
  answer: z.string().min(10, "Answer is required."),
  order: z.coerce.number().int().min(0),
  is_active: z.boolean(),
});
type ItemFormValues = z.infer<typeof itemSchema>;

interface FaqItemsClientProps {
  category: FaqCategory;
  onBack: () => void;
}

export function FaqItemsClient({ category, onBack }: FaqItemsClientProps) {
  const queryClient = useQueryClient();
  const [isDialogOpen, setDialogOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<FaqItem | null>(null);

  const queryKey = queryKeys.admin.content.faqs.itemList(category.id);

  const { data: response, isLoading } = useQuery({
    queryKey,
    queryFn: () => getFaqItems(category.id),
    enabled: !!category.id,
  });
  const items = response?.results ?? [];

  const form = useForm<ItemFormValues>({
    resolver: zodResolver(itemSchema),
    defaultValues: { question: "", answer: "", order: 0, is_active: true },
  });

  const createMutation = useMutation({
    mutationFn: createFaqItem,
    onSuccess: () => {
      toast.success("FAQ Item created!");
      queryClient.invalidateQueries({ queryKey });
      setDialogOpen(false);
    },
    onError: (err) =>
      toast.error("Failed to create item.", { description: err.message }),
  });

  const updateMutation = useMutation({
    mutationFn: updateFaqItem,
    onSuccess: () => {
      toast.success("FAQ Item updated!");
      queryClient.invalidateQueries({ queryKey });
      setDialogOpen(false);
    },
    onError: (err) =>
      toast.error("Failed to update item.", { description: err.message }),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteFaqItem,
    onSuccess: () => toast.success("FAQ Item deleted."),
    onMutate: async (idToDelete) => {
      await queryClient.cancelQueries({ queryKey });
      const previousData = queryClient.getQueryData<any>(queryKey);
      queryClient.setQueryData(queryKey, (old: any) => ({
        ...old,
        results: old.results.filter((i: FaqItem) => i.id !== idToDelete),
      }));
      return { previousData };
    },
    onError: (err, _vars, context) => {
      queryClient.setQueryData(queryKey, context?.previousData);
      toast.error("Failed to delete item.", { description: err.message });
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey }),
  });

  const handleOpenDialog = (item: FaqItem | null = null) => {
    setSelectedItem(item);
    form.reset(
      item ?? { question: "", answer: "", order: items.length, is_active: true }
    );
    setDialogOpen(true);
  };

  const onSubmit = (values: ItemFormValues) => {
    const payload = { ...values, category: category.id };
    if (selectedItem) {
      updateMutation.mutate({ id: selectedItem.id, payload });
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
              <Button
                variant="ghost"
                size="sm"
                onClick={onBack}
                className="mb-2 -ml-2"
              >
                <ArrowLeft className="h-4 w-4 ltr:mr-2 rtl:ml-2" /> Back to
                Categories
              </Button>
              <CardTitle>Items in "{category.name}"</CardTitle>
              <CardDescription>
                Manage the questions and answers for this category.
              </CardDescription>
            </div>
            <Button onClick={() => handleOpenDialog()}>
              <PlusCircle className="ltr:mr-2 rtl:ml-2 h-4 w-4" /> Add New Item
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="border rounded-md">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Order</TableHead>
                  <TableHead>Question</TableHead>
                  <TableHead>Status</TableHead>
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
                        <Skeleton className="h-5 w-96" />
                      </TableCell>
                      <TableCell>
                        <Skeleton className="h-6 w-16" />
                      </TableCell>
                      <TableCell className="text-right">
                        <Skeleton className="h-8 w-8 ml-auto" />
                      </TableCell>
                    </TableRow>
                  ))}
                {items.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>{item.order}</TableCell>
                    <TableCell className="font-medium">
                      {item.question}
                    </TableCell>
                    <TableCell>
                      <Badge variant={item.is_active ? "default" : "secondary"}>
                        {item.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu modal={false}>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" className="h-8 w-8 p-0">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            onClick={() => handleOpenDialog(item)}
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
                            title="Delete FAQ Item"
                            description={`Are you sure you want to delete the question "${item.question}"?`}
                            onConfirm={() => deleteMutation.mutate(item.id)}
                            isConfirming={
                              deleteMutation.isPending &&
                              selectedItem?.id === item.id
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
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {selectedItem ? "Edit FAQ Item" : "New FAQ Item"}
            </DialogTitle>
          </DialogHeader>
          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(onSubmit)}
              className="space-y-4 py-4 max-h-[70vh] overflow-y-auto px-2"
            >
              <FormField
                name="question"
                control={form.control}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Question</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                name="answer"
                control={form.control}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Answer</FormLabel>
                    <FormControl>
                      <Textarea rows={5} {...field} />
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
              <FormField
                name="is_active"
                control={form.control}
                render={({ field }) => (
                  <FormItem className="flex items-center justify-between rounded-lg border p-3">
                    <FormLabel>Active</FormLabel>
                    <FormControl>
                      <Switch
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />
              <DialogFooter className="sticky bottom-0 bg-background pt-4">
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
