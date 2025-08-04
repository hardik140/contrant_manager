import type React from "react";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

// Load font
const inter = Inter({ subsets: ["latin"] });

// Metadata for SEO and browser
export const metadata: Metadata = {
  title: "Contract Intelligence Suite",
  description: "AI-powered contract summarization and policy comparison tools",
};

// Default layout
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head />
      <body className={inter.className}>
        <main>{children}</main>
      </body>
    </html>
  );
}
