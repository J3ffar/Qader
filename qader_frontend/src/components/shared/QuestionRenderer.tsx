"use client";

import { RichContentViewer } from "@/components/shared/RichContentViewer";

interface QuestionRendererProps {
  questionText: string;
  imageUrl: string | null;
}

export const QuestionRenderer = ({
  questionText,
  imageUrl,
}: QuestionRendererProps) => {
  return (
    <div className="space-y-4">
      {imageUrl && (
        <div className="flex justify-center">
          <img
            src={imageUrl}
            alt="Question illustration"
            className="max-w-full max-h-64 rounded-md border object-contain"
          />
        </div>
      )}
      {/* Apply large typography styles for the main question text */}
      <RichContentViewer
        htmlContent={questionText}
        className="prose prose-lg dark:prose-invert max-w-none text-right rtl:text-right"
      />
    </div>
  );
};
