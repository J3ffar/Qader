"use client";

import { type Editor } from "@tiptap/react";
import {
  Bold,
  Strikethrough,
  Italic,
  List,
  ListOrdered,
  Heading3,
} from "lucide-react";
import { useTranslations } from "next-intl";

import { Toggle } from "@/components/ui/toggle";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

type Props = {
  editor: Editor | null;
};

export function EditorToolbar({ editor }: Props) {
  const t = useTranslations("Admin.Content.toolbar");

  if (!editor) {
    return null;
  }

  const toolbarItems = [
    {
      name: "heading3",
      icon: Heading3,
      isActive: () => editor.isActive("heading", { level: 3 }),
      action: () => editor.chain().focus().toggleHeading({ level: 3 }).run(),
    },
    {
      name: "bold",
      icon: Bold,
      isActive: () => editor.isActive("bold"),
      action: () => editor.chain().focus().toggleBold().run(),
    },
    {
      name: "italic",
      icon: Italic,
      isActive: () => editor.isActive("italic"),
      action: () => editor.chain().focus().toggleItalic().run(),
    },
    {
      name: "strike",
      icon: Strikethrough,
      isActive: () => editor.isActive("strike"),
      action: () => editor.chain().focus().toggleStrike().run(),
    },
    {
      name: "bulletList",
      icon: List,
      isActive: () => editor.isActive("bulletList"),
      action: () => editor.chain().focus().toggleBulletList().run(),
    },
    {
      name: "orderedList",
      icon: ListOrdered,
      isActive: () => editor.isActive("orderedList"),
      action: () => editor.chain().focus().toggleOrderedList().run(),
    },
  ];

  return (
    <TooltipProvider delayDuration={100}>
      <div className="border border-input bg-transparent rounded-t-md p-1 flex items-center gap-1 flex-wrap">
        {toolbarItems.map((item) => (
          <Tooltip key={item.name}>
            <TooltipTrigger asChild>
              <Toggle
                size="sm"
                pressed={item.isActive()}
                onPressedChange={item.action}
                aria-label={t(item.name as any)}
              >
                <item.icon className="h-4 w-4" />
              </Toggle>
            </TooltipTrigger>
            <TooltipContent>
              <p>{t(item.name as any)}</p>
            </TooltipContent>
          </Tooltip>
        ))}
      </div>
    </TooltipProvider>
  );
}
