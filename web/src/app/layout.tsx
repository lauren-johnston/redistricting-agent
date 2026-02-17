import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Redistricting Dashboard",
  description: "Community of Interest submissions from the redistricting voice agent",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
