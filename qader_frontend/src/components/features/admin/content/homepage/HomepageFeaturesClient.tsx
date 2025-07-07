"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { toast } from "sonner";
import { MoreHorizontal, PlusCircle } from "lucide-react";

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
  DialogDescription,
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

// Zod Schema for validation
const featureSchema = z.object({
  title: z.string().min(3, "Title is required."),
  text: z.string().min(10, "Text description is required."),
  icon_class: z.string().optional().nullable(),
  order: z.coerce.number().int().min(0),
  is_active: z.boolean(),
});
type FeatureFormValues = z.infer<typeof featureSchema>;

export function HomepageFeaturesClient() {
  const queryClient = useQueryClient();
  const [isDialogOpen, setDialogOpen] = useState(false);
  const [selectedFeature, setSelectedFeature] =
    useState<HomepageFeatureCard | null>(null);

  const { data: response, isLoading } = useQuery({
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

  // --- MUTATIONS ---
  const createMutation = useMutation({
    mutationFn: createHomepageFeature,
    onSuccess: () => {
      toast.success("Feature card created successfully!");
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.content.homepage.features(),
      });
      setDialogOpen(false);
    },
    onError: (err) =>
      toast.error("Failed to create feature.", { description: err.message }),
  });

  const updateMutation = useMutation({
    mutationFn: updateHomepageFeature,
    onSuccess: () => {
      toast.success("Feature card updated successfully!");
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.content.homepage.features(),
      });
      setDialogOpen(false);
    },
    onError: (err) =>
      toast.error("Failed to update feature.", { description: err.message }),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteHomepageFeature,
    onSuccess: () => {
      toast.success("Feature card deleted.");
    },
    // Optimistic Update
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

  // --- HANDLERS ---
  const handleOpenDialog = (feature: HomepageFeatureCard | null = null) => {
    setSelectedFeature(feature);
    if (feature) {
      form.reset(feature);
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
              <CardTitle>Homepage Feature Cards</CardTitle>
              <CardDescription>
                Items appearing in the 'Why Choose Us' section.
              </CardDescription>
            </div>
            <Button onClick={() => handleOpenDialog()}>
              <PlusCircle className="ltr:mr-2 rtl:ml-2 h-4 w-4" /> Add New Card
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="border rounded-md">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Order</TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead className="hidden md:table-cell">Text</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>
                    <span className="sr-only">Actions</span>
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
                {features.map((feature) => (
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
                        {feature.is_active ? "Active" : "Inactive"}
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
                          <DropdownMenuLabel>Actions</DropdownMenuLabel>
                          <DropdownMenuItem
                            onClick={() => handleOpenDialog(feature)}
                          >
                            Edit
                          </DropdownMenuItem>
                          <ConfirmationDialog
                            triggerButton={
                              <DropdownMenuItem
                                className="text-destructive"
                                onSelect={(e) => e.preventDefault()} // Prevents DropdownMenu from closing
                              >
                                Delete
                              </DropdownMenuItem>
                            }
                            title="Delete Feature Card"
                            description={`Are you sure you want to delete the card "${feature.title}"? This action cannot be undone.`}
                            onConfirm={() => deleteMutation.mutate(feature.id)}
                            isConfirming={
                              deleteMutation.isPending &&
                              selectedFeature?.id === feature.id
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

      {/* Create/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>
              {selectedFeature
                ? "Edit Feature Card"
                : "Create New Feature Card"}
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
                    <FormLabel>Title</FormLabel>
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
                    <FormLabel>Text</FormLabel>
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
                    <FormLabel>Icon Class (e.g., fas fa-book)</FormLabel>
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
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3">
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
