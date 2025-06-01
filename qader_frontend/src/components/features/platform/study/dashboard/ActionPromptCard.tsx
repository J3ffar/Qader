import React from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import Link from "next/link";

interface ActionPromptCardProps {
  title: string;
  description: string;
  buttonText: string;
  buttonHref: string;
  icon?: React.ElementType;
  className?: string;
}

export const ActionPromptCard: React.FC<ActionPromptCardProps> = ({
  title,
  description,
  buttonText,
  buttonHref,
  icon: Icon,
  className,
}) => {
  return (
    <Card className={cn("w-full max-w-lg mx-auto", className)}>
      <CardHeader className="items-center text-center">
        {Icon && <Icon className="mb-4 h-12 w-12 text-primary" />}
        <CardTitle className="text-2xl">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        {/* Additional content can go here if needed */}
      </CardContent>
      <CardFooter className="flex justify-center">
        <Button asChild size="lg">
          <Link href={buttonHref}>{buttonText}</Link>
        </Button>
      </CardFooter>
    </Card>
  );
};
