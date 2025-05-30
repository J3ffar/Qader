// src/hooks/useOnClickOutside.ts
import { useEffect, RefObject } from "react";

type EventType = MouseEvent | TouchEvent;

export function useOnClickOutside<T extends HTMLElement = HTMLElement>(
  dropdownRef: RefObject<T | null>,
  triggerRef: RefObject<HTMLElement | null>, // Ref for the element that triggers the dropdown
  handler: (event: EventType) => void,
  enabled: boolean = true // Allow enabling/disabling the hook
): void {
  useEffect(() => {
    if (!enabled) {
      return;
    }

    const listener = (event: EventType) => {
      const targetElement = event.target as Node;

      // Do nothing if clicking dropdown's element or descendent elements
      if (dropdownRef.current && dropdownRef.current.contains(targetElement)) {
        return;
      }

      // Do nothing if clicking trigger's element or descendent elements
      if (triggerRef.current && triggerRef.current.contains(targetElement)) {
        return;
      }

      handler(event);
    };

    document.addEventListener("mousedown", listener);
    document.addEventListener("touchstart", listener);

    return () => {
      document.removeEventListener("mousedown", listener);
      document.removeEventListener("touchstart", listener);
    };
  }, [dropdownRef, triggerRef, handler, enabled]); // Reload only if refs, handler, or enabled state changes
}
