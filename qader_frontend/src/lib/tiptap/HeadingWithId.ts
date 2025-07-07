import { Heading } from "@tiptap/extension-heading";
import { Plugin } from "@tiptap/pm/state";

// Helper function remains the same
const createSlug = (text: string) => {
  return text
    .toString()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim()
    .replace(/\s+/g, "-")
    .replace(/[^\w-]+/g, "")
    .replace(/--+/g, "-");
};

export const HeadingWithId = Heading.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      id: {
        default: null,
        parseHTML: (element) => element.getAttribute("id"),
      },
    };
  },

  addProseMirrorPlugins() {
    return [
      new Plugin({
        appendTransaction: (transactions, oldState, newState) => {
          if (!newState.doc.eq(oldState.doc)) {
            let tr = newState.tr;
            let modified = false;

            newState.doc.descendants((node, pos) => {
              if (node.type.name === this.name) {
                // *** THIS IS THE CORRECTED LOGIC ***

                // 1. Generate the expected ID from the current text content.
                const expectedId = createSlug(node.textContent);

                // 2. Get the current ID from the node's attributes.
                const currentId = node.attrs.id;

                // 3. If there's text, and the expected ID does not match the current ID,
                //    then we need to update it. This covers both missing IDs and outdated IDs.
                if (
                  node.textContent.trim().length > 0 &&
                  expectedId !== currentId
                ) {
                  tr = tr.setNodeMarkup(pos, undefined, {
                    ...node.attrs,
                    id: expectedId,
                  });
                  modified = true;
                }
              }
            });

            return modified ? tr : null;
          }
          return null;
        },
      }),
    ];
  },
});
