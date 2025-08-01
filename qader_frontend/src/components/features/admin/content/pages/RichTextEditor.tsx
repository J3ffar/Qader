"use client";

import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { EditorToolbar } from "./EditorToolbar";
import { useEffect } from "react";
import { HeadingWithId } from "@/lib/tiptap/HeadingWithId"; // Import our custom extension

// These styles are a bit simpler now as we rely more on Tailwind Prose
const editorStyles = `
  .ProseMirror {
    min-height: 250px;
    padding: 1rem 1.25rem; /* Match prose padding */
    border: 1px solid hsl(var(--input));
    border-top: none;
    border-radius: 0 0 0.375rem 0.375rem;
    outline: none;
    transition: border-color 0.2s;
  }
  .ProseMirror:focus {
    border-color: hsl(var(--ring));
  }
  /* Remove default prose margins for a cleaner editor experience */
  .ProseMirror > * {
    margin: 0;
  }
  .ProseMirror > * + * {
    margin-top: 1.25em; /* Match prose spacing */
  }
`;

interface RichTextEditorProps {
  value: string;
  onChange: (richText: string) => void;
}

export function RichTextEditor({ value, onChange }: RichTextEditorProps) {
  const editor = useEditor({
    extensions: [
      // Configure StarterKit to use our custom Heading extension instead of the default one
      StarterKit.configure({
        heading: false, // Disable the default heading
      }),
      HeadingWithId.configure({
        // We only need h3 as per the ConditionsClient
        levels: [3],
      }),
    ],
    editorProps: {
      attributes: {
        // *** FIX 1: APPLY THE CORRECT PROSE CLASSES ***
        // Use `prose-lg` to match the display component.
        class: "prose-lg dark:prose-invert max-w-none",
      },
    },
    onUpdate({ editor }) {
      if (editor.getHTML() === value) return;
      onChange(editor.getHTML());
    },
    content: value, // content should be passed at initialization
  });

  useEffect(() => {
    if (editor && editor.getHTML() !== value) {
      editor.commands.setContent(value);
    }
  }, [value, editor]);

  return (
    <div>
      <style>{editorStyles}</style>
      <EditorToolbar editor={editor} />
      <EditorContent className="border rounded-b-md" editor={editor} />
    </div>
  );
}
