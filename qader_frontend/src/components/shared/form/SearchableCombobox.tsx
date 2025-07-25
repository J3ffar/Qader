import * as React from "react";
import { FieldValues, Path, PathValue, UseFormReturn } from "react-hook-form";
import { Check, ChevronsUpDown } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

interface ComboboxOption {
  id: number;
  name: string;
}

interface SearchableComboboxProps<TFormValues extends FieldValues> {
  form: UseFormReturn<TFormValues>;
  fieldName: Path<TFormValues>;
  label: string;
  options: ComboboxOption[];
  placeholder: string;
  searchPlaceholder: string;
  emptyMessage: string;
  onValueChange?: (value: number | undefined) => void;
  isLoading?: boolean;
  disabled?: boolean;
}

export function SearchableCombobox<TFormValues extends FieldValues>({
  form,
  fieldName,
  label,
  options,
  placeholder,
  searchPlaceholder,
  emptyMessage,
  onValueChange,
  isLoading = false,
  disabled = false,
}: SearchableComboboxProps<TFormValues>) {
  const [open, setOpen] = React.useState(false);
  return (
    <FormField
      control={form.control}
      name={fieldName}
      render={({ field }) => (
        <FormItem>
          <FormLabel>{label}</FormLabel>
          <Popover open={open} onOpenChange={setOpen} modal={true}>
            <PopoverTrigger asChild>
              <FormControl>
                <Button
                  variant="outline"
                  role="combobox"
                  aria-expanded={open}
                  className={cn(
                    "w-full justify-between font-normal",
                    !field.value && "text-muted-foreground"
                  )}
                  disabled={disabled || isLoading}
                >
                  {isLoading
                    ? "جار التحميل..."
                    : field.value
                    ? options.find((option) => option.id === field.value)?.name
                    : placeholder}
                  <ChevronsUpDown className="ms-2 h-4 w-4 shrink-0 opacity-50" />
                </Button>
              </FormControl>
            </PopoverTrigger>
            <PopoverContent
              className="w-[--radix-popover-trigger-width] p-0"
              align="start"
              onPointerDownOutside={(e) => {
                e.preventDefault();
              }}
            >
              {/* --- THE FIX FOR SEARCHING IS HERE --- */}
              <Command
                filter={(value, search) => {
                  // `value` is the string from `CommandItem`'s `value` prop
                  // `search` is the string the user types in `CommandInput`
                  // Return 1 for a match, 0 for no match.
                  if (value.toLowerCase().includes(search.toLowerCase())) {
                    return 1;
                  }
                  return 0;
                }}
              >
                {/* <CommandInput
                  placeholder={searchPlaceholder}
                  aria-label={searchPlaceholder}
                /> */}
                <CommandList>
                  {isLoading ? (
                    <div className="py-6 text-center text-sm">
                      جار تحميل البيانات...
                    </div>
                  ) : (
                    <>
                      <CommandEmpty>{emptyMessage}</CommandEmpty>
                      <CommandGroup>
                        {options.map((option) => (
                          <CommandItem
                            // The `value` prop is used by the `filter` function above
                            value={option.name}
                            key={option.id}
                            onSelect={() => {
                              const selectedValue =
                                option.id === field.value
                                  ? undefined
                                  : option.id;

                              form.setValue(
                                fieldName,
                                selectedValue as PathValue<
                                  TFormValues,
                                  Path<TFormValues>
                                >,
                                { shouldValidate: true }
                              );

                              if (onValueChange) {
                                onValueChange(selectedValue);
                              }
                              setOpen(false);
                            }}
                          >
                            <Check
                              className={cn(
                                "me-2 h-4 w-4",
                                option.id === field.value
                                  ? "opacity-100"
                                  : "opacity-0"
                              )}
                            />
                            {option.name}
                          </CommandItem>
                        ))}
                      </CommandGroup>
                    </>
                  )}
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>
          <FormMessage />
        </FormItem>
      )}
    />
  );
}
