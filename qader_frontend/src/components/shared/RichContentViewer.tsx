"use client";

import { useRef, useEffect } from "react";
import katex from "katex";
import { cn } from "@/lib/utils";

interface RichContentViewerProps {
  htmlContent: string | null;
  className?: string; // Prop to allow custom styling
}

export const RichContentViewer = ({
  htmlContent,
  className,
}: RichContentViewerProps) => {
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // This effect runs whenever the htmlContent changes.
    if (contentRef.current && htmlContent) {
      // 1. Create a temporary, in-memory div to parse the incoming HTML string.
      const tempDiv = document.createElement("div");
      tempDiv.innerHTML = htmlContent;

      // 2. Use the robust querySelectorAll to find all our custom KaTeX nodes.
      const katexNodes = tempDiv.querySelectorAll<HTMLElement>(
        "span[data-katex-node]"
      );

      // 3. Iterate over each found node to render KaTeX.
      katexNodes.forEach((node) => {
        const latex = node.dataset.latex || "";
        if (latex) {
          try {
            // 4. Render the formula directly into a new span.
            const katexElement = document.createElement("span");
            katex.render(latex, katexElement, {
              throwOnError: false,
              displayMode: false,
            });
            // 5. Replace the placeholder node with the fully rendered KaTeX element.
            node.replaceWith(katexElement);
          } catch (e) {
            console.error("KaTeX rendering error:", e);
            node.textContent = `[Error: ${latex}]`;
          }
        }
      });

      // 6. Clear the actual on-screen div and append the fully processed content.
      contentRef.current.innerHTML = "";
      contentRef.current.appendChild(tempDiv);
    }
  }, [htmlContent]);

  if (!htmlContent) return null;

  // The final div is now a container that gets its content managed by the effect.
  // We pass the className prop to it for flexible styling.
  return <div ref={contentRef} className={cn(className, "relative")} />;
};
