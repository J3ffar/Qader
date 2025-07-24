"use client";

import { useState } from "react";
import { useEditor, EditorContent, Editor, Range } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Placeholder from "@tiptap/extension-placeholder";
import { Bold, Italic, List, ListOrdered, Sigma } from "lucide-react";

import { cn } from "@/lib/utils";
import { Toggle } from "@/components/ui/toggle";
import { Button } from "@/components/ui/button";
import { KatexNode } from "@/lib/tiptap-extensions/KatexNode"; // <-- Import custom node
import { EquationEditorDialog } from "./EquationEditorDialog"; // <-- Import dialog

interface RichTextEditorProps {
  value: string;
  onChange: (richText: string) => void;
  placeholder?: string;
  className?: string;
}

const Toolbar = ({ editor }: { editor: Editor | null }) => {
  const [isEquationEditorOpen, setIsEquationEditorOpen] = useState(false);
  const [selectionRange, setSelectionRange] = useState<Range | null>(null);

  if (!editor) return null;

  const handleEquationSubmit = (latex: string) => {
    // We now have a pristine `selectionRange` that was saved before the dialog opened.
    // We can use this to execute our command with precision.
    editor
      .chain()
      .focus() // Always focus the editor first
      // Pass the saved range DIRECTLY into our custom command.
      // This bypasses any reliance on the editor's current (and stale) selection state.
      .setKatex({ latex, range: selectionRange || undefined })
      .run();
  };

  const openEquationEditor = () => {
    // Capture the exact selection from the editor's state *before* it loses focus.
    const { from, to, empty } = editor.state.selection;

    // If the selection is empty (just a cursor), we don't need to save a range.
    // Our command will correctly insert at the cursor position.
    // If there IS a selection, we save it.
    setSelectionRange(empty ? null : { from, to });

    setIsEquationEditorOpen(true);
  };

  return (
    <>
      <EquationEditorDialog
        isOpen={isEquationEditorOpen}
        onClose={() => setIsEquationEditorOpen(false)}
        onSubmit={handleEquationSubmit}
      />
      <div className="flex flex-wrap items-center gap-1 rounded-t-md border border-b-0 border-input bg-transparent p-2">
        <Toggle
          size="sm"
          pressed={editor.isActive("bold")}
          onPressedChange={() => editor.chain().focus().toggleBold().run()}
        >
          <Bold className="h-4 w-4" />
        </Toggle>
        <Toggle
          size="sm"
          pressed={editor.isActive("italic")}
          onPressedChange={() => editor.chain().focus().toggleItalic().run()}
        >
          <Italic className="h-4 w-4" />
        </Toggle>
        <Toggle
          size="sm"
          pressed={editor.isActive("bulletList")}
          onPressedChange={() =>
            editor.chain().focus().toggleBulletList().run()
          }
        >
          <List className="h-4 w-4" />
        </Toggle>
        <Toggle
          size="sm"
          pressed={editor.isActive("orderedList")}
          onPressedChange={() =>
            editor.chain().focus().toggleOrderedList().run()
          }
        >
          <ListOrdered className="h-4 w-4" />
        </Toggle>
        <Button
          type="button"
          size="sm"
          variant="ghost"
          onClick={openEquationEditor}
        >
          <Sigma className="h-4 w-4" />
        </Button>
      </div>
    </>
  );
};

export const RichTextEditor = ({
  value,
  onChange,
  placeholder,
  className,
}: RichTextEditorProps) => {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({ heading: false, codeBlock: false }),
      Placeholder.configure({ placeholder: placeholder || "اكتب هنا..." }),
      KatexNode, // <-- Use our custom node
    ],
    content: value,
    editorProps: {
      attributes: {
        class: cn(
          "min-h-[80px] w-full rounded-b-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50",
          className
        ),
      },
    },
    onUpdate({ editor }) {
      onChange(editor.getHTML());
    },
  });

  return (
    <div className="flex flex-col">
      <Toolbar editor={editor} />
      <EditorContent editor={editor} />
    </div>
  );
};
