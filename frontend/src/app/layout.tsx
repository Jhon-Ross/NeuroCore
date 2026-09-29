import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "Prometeu · NeuroCore — Cérebro de IA Local",
  description:
    "Prometeu, cérebro de IA pessoal 100% local. 7 regiões cerebrais. AMD RX 7600.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-bg0 text-foreground selection:bg-accent selection:text-bg0`}
      >
        {children}
      </body>
    </html>
  );
}

