import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import LauncherShell from "../components/LauncherShell";

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
  title: "NeuroCore — Painel de Controle",
  description:
    "Launcher Desktop NeuroCore/Prometeu: Ligar, Monitorar, Logs e Chat.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" className="dark" suppressHydrationWarning>
      <body
        suppressHydrationWarning
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-bg0 text-foreground selection:bg-accent selection:text-bg0`}
      >
        <LauncherShell>{children}</LauncherShell>
      </body>
    </html>
  );
}

