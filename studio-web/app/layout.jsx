import "./globals.css";
import { StudioProvider } from "@/components/studio-context";
import { StudioShell } from "@/components/studio-shell";

export const metadata = {
  title: "AutoQuant Studio",
  description: "Point-in-time factor research evidence workbench",
};

export const viewport = {
  themeColor: "#0b1118",
};

export default function RootLayout({ children }) {
  return (
    <html lang="zh-CN">
      <body>
        <StudioProvider>
          <StudioShell>{children}</StudioShell>
        </StudioProvider>
      </body>
    </html>
  );
}
