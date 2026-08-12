import "@mantine/core/styles.css";
import "./globals.css";
import { ColorSchemeScript, MantineProvider, mantineHtmlProps } from "@mantine/core";
import { StudioProvider } from "@/components/studio-context";
import { StudioShell } from "@/components/studio-shell";
import { autoQuantTheme } from "@/lib/theme";

export const metadata = {
  title: "AutoQuant Studio",
  description: "Point-in-time factor research evidence workbench",
};

export const viewport = {
  themeColor: "#0b1118",
};

export default function RootLayout({ children }) {
  return (
    <html lang="zh-CN" {...mantineHtmlProps}>
      <head>
        <ColorSchemeScript defaultColorScheme="dark" />
      </head>
      <body>
        <MantineProvider theme={autoQuantTheme} defaultColorScheme="dark" forceColorScheme="dark">
          <StudioProvider>
            <StudioShell>{children}</StudioShell>
          </StudioProvider>
        </MantineProvider>
      </body>
    </html>
  );
}
