import { createTheme } from "@mantine/core";

export const autoQuantTheme = createTheme({
  primaryColor: "cyan",
  defaultRadius: "xs",
  fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  fontFamilyMonospace: "'IBM Plex Mono', 'SFMono-Regular', Consolas, 'Liberation Mono', monospace",
  headings: {
    fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    fontWeight: "650",
  },
  spacing: {
    xs: "0.4rem",
    sm: "0.6rem",
    md: "0.85rem",
    lg: "1.1rem",
    xl: "1.5rem",
  },
});
