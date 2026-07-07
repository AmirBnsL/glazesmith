import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "GlazeSmith | AI Glaze Chemistry Agent",
  description: "AI-powered ceramic glaze formulation, defect diagnosis, and image generation",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-stone-950 text-stone-100 min-h-screen antialiased">{children}</body>
    </html>
  );
}
