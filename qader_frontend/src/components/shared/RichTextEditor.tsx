"use client";

import { useEffect, useState } from "react";
import { useEditor, EditorContent, Editor, Range } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Placeholder from "@tiptap/extension-placeholder";
import Underline from "@tiptap/extension-underline";
import TextAlign from "@tiptap/extension-text-align";
import Highlight from "@tiptap/extension-highlight";
import {
  Bold,
  Italic,
  List,
  ListOrdered,
  Sigma,
  Underline as UnderlineIcon,
  Strikethrough,
  Heading2,
  Heading3,
  AlignLeft,
  AlignCenter,
  AlignRight,
  Highlighter,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { Toggle } from "@/components/ui/toggle";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { KatexNode } from "@/lib/tiptap-extensions/KatexNode";
import { EquationEditorDialog } from "./EquationEditorDialog";

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
    editor
      .chain()
      .focus()
      .setKatex({ latex, range: selectionRange || undefined })
      .run();
  };

  const openEquationEditor = () => {
    const { from, to, empty } = editor.state.selection;
    setSelectionRange(empty ? null : { from, to });

    if (editor.isActive("katex")) {
      const existingLatex = editor.getAttributes("katex").latex;
      setEditingLatex(existingLatex);
    } else {
      setEditingLatex("");
    }

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
      <div className="flex flex-nowrap items-center gap-1 rounded-t-md border border-b-0 border-input bg-transparent p-2 overflow-x-auto">
        {/* Basic Styles */}
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
          pressed={editor.isActive("underline")}
          onPressedChange={() => editor.chain().focus().toggleUnderline().run()}
        >
          <UnderlineIcon className="h-4 w-4" />
        </Toggle>
        <Toggle
          size="sm"
          pressed={editor.isActive("strike")}
          onPressedChange={() => editor.chain().focus().toggleStrike().run()}
        >
          <Strikethrough className="h-4 w-4" />
        </Toggle>
        <Toggle
          size="sm"
          pressed={editor.isActive("highlight")}
          onPressedChange={() => editor.chain().focus().toggleHighlight().run()}
        >
          <Highlighter className="h-4 w-4" />
        </Toggle>

        <Separator orientation="vertical" className="h-6 mx-1" />

        {/* Special */}
        <Button
          type="button"
          size="sm"
          variant="ghost"
          onClick={openEquationEditor}
        >
          <Sigma className="h-4 w-4" />
        </Button>

        <Separator orientation="vertical" className="h-6 mx-1" />

        {/* Headings */}
        <Toggle
          size="sm"
          pressed={editor.isActive("heading", { level: 2 })}
          onPressedChange={() =>
            editor.chain().focus().toggleHeading({ level: 2 }).run()
          }
        >
          <Heading2 className="h-4 w-4" />
        </Toggle>
        <Toggle
          size="sm"
          pressed={editor.isActive("heading", { level: 3 })}
          onPressedChange={() =>
            editor.chain().focus().toggleHeading({ level: 3 }).run()
          }
        >
          <Heading3 className="h-4 w-4" />
        </Toggle>

        <Separator orientation="vertical" className="h-6 mx-1" />

        {/* Alignment */}
        <Toggle
          size="sm"
          pressed={editor.isActive({ textAlign: "left" })}
          onPressedChange={() =>
            editor.chain().focus().setTextAlign("left").run()
          }
        >
          <AlignLeft className="h-4 w-4" />
        </Toggle>
        <Toggle
          size="sm"
          pressed={editor.isActive({ textAlign: "center" })}
          onPressedChange={() =>
            editor.chain().focus().setTextAlign("center").run()
          }
        >
          <AlignCenter className="h-4 w-4" />
        </Toggle>
        <Toggle
          size="sm"
          pressed={editor.isActive({ textAlign: "right" })}
          onPressedChange={() =>
            editor.chain().focus().setTextAlign("right").run()
          }
        >
          <AlignRight className="h-4 w-4" />
        </Toggle>

        <Separator orientation="vertical" className="h-6 mx-1" />

        {/* Lists */}
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
      StarterKit.configure({
        heading: { levels: [2, 3] }, // Enable H2, H3
        strike: {}, // Enable strikethrough
        codeBlock: false, // Keep disabled
      }),
      Underline,
      TextAlign.configure({
        types: ["heading", "paragraph"],
      }),
      Highlight,
      Placeholder.configure({ placeholder: placeholder || "اكتب هنا..." }),
      KatexNode,
    ],
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
    immediatelyRender: false,
  });

  useEffect(() => {
    if (!editor || !value) {
      return;
    }

    if (editor.getHTML() !== value) {
      editor.commands.setContent(value);
    }
  }, [editor, value]);

  return (
    <div className="flex flex-col min-w-0">
      <Toolbar editor={editor} />
      <EditorContent editor={editor} />
    </div>
  );
};
