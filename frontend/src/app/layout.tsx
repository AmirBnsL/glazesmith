import type { Metadata } from "next";
import { Fraunces, Plus_Jakarta_Sans, Caveat } from "next/font/google";
import { ThemeProvider } from "next-themes";
import { cn } from "@/lib/utils";
import "./globals.css";

const displayFont = Fraunces({ subsets: ["latin"], variable: "--font-display", weight: ["500", "600"] });
const bodyFont = Plus_Jakarta_Sans({ subsets: ["latin"], variable: "--font-sans" });
const accentFont = Caveat({ subsets: ["latin"], variable: "--font-accent" });

export const metadata: Metadata = {
  title: "GlazeSmith | AI Glaze Chemistry Agent",
  description: "AI-powered ceramic glaze formulation, defect diagnosis, and image generation",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={cn(bodyFont.variable, displayFont.variable, accentFont.variable)} suppressHydrationWarning>
      <body className="font-sans bg-[var(--bg-dream)] text-[var(--ink)] min-h-screen antialiased">
        <ThemeProvider attribute="data-theme" themes={["light","kiln","plum","indigo"]} defaultTheme="light" enableSystem={false}>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
