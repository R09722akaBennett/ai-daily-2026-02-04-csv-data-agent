import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "KDoc IDP",
  description: "Self-hosted IDP service powered by Docling — turn messy enterprise documents into LLM-ready Markdown, JSON, and tables.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="h-full">{children}</body>
    </html>
  );
}
