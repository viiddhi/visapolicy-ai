import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Visapolicy.ai — Real-time immigration alerts",
  description: "Stay informed about USCIS rule changes that affect your visa status",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 antialiased">{children}</body>
    </html>
  );
}
