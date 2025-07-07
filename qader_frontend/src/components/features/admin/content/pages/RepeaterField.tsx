"use client";

import { useFieldArray, UseFormReturn } from "react-hook-form"; // Import UseFormReturn
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { PlusCircle, Trash2 } from "lucide-react";

interface RepeaterFieldProps {
  form: UseFormReturn<any>; // FIX: Change prop from 'control' to 'form'
  name: string;
  label: string;
  initialData: any[] | null;
}

export function RepeaterField({
  form,
  name,
  label,
  initialData,
}: RepeaterFieldProps) {
  const { control, getValues } = form; // Destructure control and getValues from the form object

  const { fields, append, remove } = useFieldArray({
    control, // useFieldArray still needs the control object
    name,
  });

  const handleAddItem = () => {
    let newItemTemplate = {};
    if (initialData && initialData.length > 0) {
      newItemTemplate = Object.keys(initialData[0]).reduce((acc, key) => {
        acc[key] = "";
        return acc;
      }, {} as Record<string, any>);
    } else if (fields.length > 0) {
      // FIX: Use getValues from the destructured form object
      const firstField = getValues(name)[0];
      if (firstField) {
        newItemTemplate = Object.keys(firstField).reduce((acc, key) => {
          acc[key] = "";
          return acc;
        }, {} as Record<string, any>);
      }
    }
    append(newItemTemplate);
  };

  const renderInputForValue = (value: unknown) => {
    if (typeof value === "string" && value.length > 100) {
      return Textarea;
    }
    return Input;
  };

  return (
    <Card className="bg-muted/30">
      <CardHeader className="flex flex-row items-center justify-between pb-4">
        <CardTitle className="text-lg">{label}</CardTitle>
        <Button
          type="button"
          size="sm"
          variant="outline"
          onClick={handleAddItem}
        >
          <PlusCircle className="ltr:mr-2 rtl:ml-2 h-4 w-4" />
          Add Item
        </Button>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {fields.map((item, index) => (
            <div
              key={item.id}
              className="p-4 border rounded-md bg-background relative"
            >
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="absolute top-2 rtl:left-2 ltr:right-2 h-7 w-7 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                onClick={() => remove(index)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
              <div className="space-y-4 pr-10">
                {/* FIX: Use getValues from the destructured form object */}
                {Object.keys(getValues(`${name}.${index}`)).map((key) => {
                  const InputComponent = renderInputForValue(
                    getValues(`${name}.${index}.${key}`)
                  );
                  return (
                    <FormField
                      key={key}
                      control={control}
                      name={`${name}.${index}.${key}` as const}
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="capitalize">
                            {key.replace(/_/g, " ")}
                          </FormLabel>
                          <FormControl>
                            <InputComponent
                              {...field}
                              value={field.value ?? ""}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  );
                })}
              </div>
            </div>
          ))}
          {fields.length === 0 && (
            <p className="text-center text-sm text-muted-foreground py-4">
              No items yet. Click "Add Item" to begin.
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
