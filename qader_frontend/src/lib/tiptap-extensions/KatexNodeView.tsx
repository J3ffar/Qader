// src/lib/tiptap-extensions/KatexNodeView.tsx
"use client";

import { NodeViewWrapper } from "@tiptap/react";
import katex from "katex";
import { useEffect, useRef } from "react";

export const KatexNodeView = ({
  node: {
    attrs: { latex },
  },
  selected,
}: any) => {
  const katexRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (katexRef.current) {
      try {
        katex.render(latex, katexRef.current, {
          throwOnError: false,
          displayMode: false,
        });
      } catch (error) {
        katexRef.current.innerHTML = `<span class="text-red-500">Error</span>`;
        console.error(error);
      }
    }
  }, [latex]);

  return (
    <NodeViewWrapper
      as="span"
      // --- UX IMPROVEMENT: Add a title to show raw LaTeX on hover ---
      title={latex}
      // -------------------------------------------------------------
      className={`react-component ${
        selected ? "ProseMirror-selectednode" : ""
      }`}
    >
      <span ref={katexRef} contentEditable={false} />
    </NodeViewWrapper>
  );
};
