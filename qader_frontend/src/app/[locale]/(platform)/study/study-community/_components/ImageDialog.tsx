"use client";

import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import Image from "next/image";

interface ImageDialogProps {
  src: string;
  alt: string;
  children: React.ReactNode;
}

export function ImageDialog({ src, alt, children }: ImageDialogProps) {
  return (
    <Dialog>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="p-0 border-0 bg-transparent max-w-4xl w-full h-auto shadow-none">
        <Image
          src={src}
          alt={alt}
          width={1200}
          height={800}
          className="rounded-lg object-contain w-full h-auto"
        />
      </DialogContent>
    </Dialog>
  );
}
