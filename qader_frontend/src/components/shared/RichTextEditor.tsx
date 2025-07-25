"use client";

import { useEffect, useState } from "react";
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
  const [editingLatex, setEditingLatex] = useState("");

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
    // Save the selection range regardless, for accurate placement.
    const { from, to, empty } = editor.state.selection;
    setSelectionRange(empty ? null : { from, to });

    // Check if the currently selected node is a 'katex' node.
    if (editor.isActive("katex")) {
      // If yes, get its attributes, which includes the 'latex' string.
      const existingLatex = editor.getAttributes("katex").latex;
      setEditingLatex(existingLatex); // Set it for the dialog
    } else {
      // If not, ensure we're in "create" mode with a blank slate.
      setEditingLatex("");
    }

    // Finally, open the dialog.
    setIsEquationEditorOpen(true);
  };

  return (
    <>
      <EquationEditorDialog
        isOpen={isEquationEditorOpen}
        onClose={() => setIsEquationEditorOpen(false)}
        onSubmit={handleEquationSubmit}
        initialValue={editingLatex}
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
      KatexNode,
    ],
    // DO NOT set content here directly when using immediatelyRender: false
    editorProps: {
      attributes: {
        class: cn(
          "min-h-[80px] w-full rounded-b-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50",
          className
        ),
      },
    },
    onUpdate({ editor }) {
      // The onChange handler is still correct
      onChange(editor.getHTML());
    },
    immediatelyRender: false,
  });

  // --- NEW useEffect TO POPULATE THE EDITOR ---
  // This effect runs after the component has mounted safely on the client.
  useEffect(() => {
    if (!editor || !value) {
      return;
    }

    // Compare the editor's current content with the value prop.
    // This check is VITAL to prevent an infinite loop. We only update
    // the content if it's different from the prop, which happens on
    // initial load or if the parent component forces a change.
    if (editor.getHTML() !== value) {
      // Use `setContent` to populate the editor. The `false` argument
      // prevents this action from triggering the `onUpdate` callback,
      // further preventing potential loops.
      editor.commands.setContent(value);
    }
  }, [editor, value]); // Rerun this effect if the editor instance or the value prop changes

  return (
    <div className="flex flex-col">
      <Toolbar editor={editor} />
      <EditorContent editor={editor} />
    </div>
  );
};
