"use client";

import { useState, useRef } from "react";
import Image from "next/image";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ImagePlus, Library, Loader2, X } from "lucide-react";

import { uploadPageImage } from "@/services/api/admin/content.service";
import { queryKeys } from "@/constants/queryKeys";
import {
  type ContentImage,
  type UploadImagePayload,
} from "@/types/api/admin/content.types";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { AspectRatio } from "@/components/ui/aspect-ratio";
import { Card, CardContent } from "@/components/ui/card";
import { Page } from "@/types/api/content.types";

interface ImageUploaderProps {
  pageSlug: string;
  allPageImages: ContentImage[];
  value: string | null; // The current image_slug from the form
  onChange: (value: string | null) => void; // RHF's onChange
}

export function ImageUploader({
  pageSlug,
  allPageImages,
  value,
  onChange,
}: ImageUploaderProps) {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isLibraryOpen, setLibraryOpen] = useState(false);

  const currentImage = allPageImages.find((img) => img.slug === value);

  const uploadMutation = useMutation({
    mutationFn: (payload: UploadImagePayload) =>
      uploadPageImage({ pageSlug, payload }),
    onSuccess: (newImage) => {
      toast.success(`Image "${newImage.name}" uploaded successfully!`);
      // Update the form with the new image slug
      onChange(newImage.slug);

      // Manually update the query cache to include the new image in the library
      // without needing to refetch the whole page.
      queryClient.setQueryData<any>(
        queryKeys.admin.content.pages.detail(pageSlug),
        (oldData: Page<any>) => {
          if (!oldData) return oldData;
          return {
            ...oldData,
            images: [...oldData.images, newImage],
          };
        }
      );
    },
    onError: (error) => {
      toast.error("Upload failed.", { description: error.message });
    },
  });

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      uploadMutation.mutate({
        image: file,
        name: file.name.replace(/\.[^/.]+$/, ""), // Use filename without extension as name
        alt_text: "Describe this image", // Admin should be able to edit this later
      });
    }
  };

  const handleSelectFromLibrary = (slug: string) => {
    onChange(slug);
    setLibraryOpen(false);
  };

  const handleRemoveImage = () => {
    onChange(null);
  };

  return (
    <Card className="overflow-hidden">
      <CardContent className="p-4">
        <div className="flex items-center gap-4">
          <div className="relative w-32 h-32 flex-shrink-0 border rounded-md flex items-center justify-center bg-muted/50">
            {uploadMutation.isPending ? (
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            ) : currentImage ? (
              <>
                <Image
                  src={currentImage.image_url}
                  alt={currentImage.alt_text || currentImage.name}
                  fill
                  className="object-cover rounded-md"
                />
                <Button
                  type="button"
                  variant="destructive"
                  size="icon"
                  className="absolute -top-2 -right-2 h-6 w-6 rounded-full z-10"
                  onClick={handleRemoveImage}
                >
                  <X className="h-4 w-4" />
                  <span className="sr-only">Remove image</span>
                </Button>
              </>
            ) : (
              <ImagePlus className="h-8 w-8 text-muted-foreground" />
            )}
          </div>
          <div className="flex flex-col gap-2">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              className="hidden"
              accept="image/png, image/jpeg, image/gif, image/svg+xml"
            />
            <Button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadMutation.isPending}
            >
              <ImagePlus className="ltr:mr-2 rtl:ml-2 h-4 w-4" />
              Upload New
            </Button>

            <Dialog open={isLibraryOpen} onOpenChange={setLibraryOpen}>
              <DialogTrigger asChild>
                <Button type="button" variant="outline">
                  <Library className="ltr:mr-2 rtl:ml-2 h-4 w-4" />
                  Choose from Library
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-4xl">
                <DialogHeader>
                  <DialogTitle>Image Library for '{pageSlug}'</DialogTitle>
                </DialogHeader>
                <ScrollArea className="h-[60vh]">
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 p-4">
                    {allPageImages.map((image) => (
                      <button
                        type="button"
                        key={image.id}
                        className="relative group focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 rounded-md"
                        onClick={() => handleSelectFromLibrary(image.slug)}
                      >
                        <AspectRatio ratio={1 / 1}>
                          <Image
                            src={image.image_url}
                            alt={image.alt_text || image.name}
                            fill
                            className="object-cover rounded-md"
                          />
                        </AspectRatio>
                        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                          <p className="text-white text-xs text-center p-1">
                            {image.name}
                          </p>
                        </div>
                      </button>
                    ))}
                  </div>
                </ScrollArea>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
