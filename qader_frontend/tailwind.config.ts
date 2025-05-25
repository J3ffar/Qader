import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}", // If you ever use `pages` dir
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/**/*.{ts,tsx}", // More encompassing for your target structure
  ],
  darkMode: "class", // This should align with next-themes
  theme: {
    extend: {
      colors: {
        // These are now primarily defined in your globals.css with CSS variables
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          // foreground: 'hsl(var(--destructive-foreground))', // Add if needed
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // ... other color mappings from your globals.css variables if needed for Tailwind intellisense
      },
      borderRadius: {
        lg: `var(--radius)`,
        md: `calc(var(--radius) - 2px)`,
        sm: `calc(var(--radius) - 4px)`,
      },
      fontFamily: {
        body: ["var(--font-body)"], // From your layout
        heading: ["var(--font-heading)"], // From your layout
      },
      // Add keyframes if not using a plugin like tw-animate-css directly
      // keyframes: {
      //   "accordion-down": { from: { height: "0" }, to: { height: "var(--radix-accordion-content-height)" } },
      //   "accordion-up": { from: { height: "var(--radix-accordion-content-height)" }, to: { height: "0" } },
      // },
      // animation: {
      //   "accordion-down": "accordion-down 0.2s ease-out",
      //   "accordion-up": "accordion-up 0.2s ease-out",
      // },
    },
  },
  plugins: [
    // require("tailwindcss-animate"), // If using this for Shadcn/ui animations rather than tw-animate-css
    // You are using tw-animate-css, which is imported in globals.css
  ],
};
export default config;
