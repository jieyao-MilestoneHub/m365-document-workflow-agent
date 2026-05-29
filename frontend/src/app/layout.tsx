import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AP Three-Way Match — Agent Console",
  description: "Agentic AP invoice three-way match for Microsoft 365 Copilot",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
