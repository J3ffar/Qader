// src/lib/tiptap-extensions/KatexNode.ts

// Make sure to import Range from @tiptap/core
import { Node, mergeAttributes, Range } from "@tiptap/core";
import { ReactNodeViewRenderer } from "@tiptap/react";
import { KatexNodeView } from "./KatexNodeView";

declare module "@tiptap/core" {
  interface Commands<ReturnType> {
    katex: {
      /**
       * Replaces content with a Katex node.
       * Can operate on a given range or the current selection.
       */
      setKatex: (options: { latex: string; range?: Range }) => ReturnType;
    };
  }
}

export const KatexNode = Node.create({
  name: "katex",
  group: "inline",
  inline: true,
  atom: true,
  defining: true,

  addAttributes() {
    return {
      latex: {
        default: "",
        parseHTML: (element) => element.getAttribute("data-latex"),
        renderHTML: (attributes) => ({ "data-latex": attributes.latex }),
      },
    };
  },

  parseHTML() {
    return [{ tag: `span[data-katex-node]` }];
  },

  renderHTML({ HTMLAttributes }) {
    return ["span", mergeAttributes(HTMLAttributes, { "data-katex-node": "" })];
  },

  // --- THIS IS THE KEY CHANGE ---
  addCommands() {
    return {
      setKatex:
        (options) =>
        ({ commands, state }) => {
          // Determine the range to operate on.
          // PRIORITY 1: Use the range explicitly passed in the options.
          // PRIORITY 2: Fall back to the editor's current selection if no range is given.
          const range = options.range || state.selection;

          // Perform the atomic replacement at the determined range.
          return commands.insertContentAt(
            range,
            {
              type: this.name,
              attrs: { latex: options.latex },
            },
            {
              // For good UX, place the cursor right after the newly inserted node.
              updateSelection: true,
            }
          );
        },
    };
  },
  // -----------------------------

  addNodeView() {
    return ReactNodeViewRenderer(KatexNodeView);
  },
});
