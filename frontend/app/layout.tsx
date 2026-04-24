import type { Metadata } from "next";
import { PlatformNav } from "@/components/platform-nav";
import { IBM_Plex_Mono, Sora } from "next/font/google";
import "./globals.css";

const displayFont = Sora({
  variable: "--font-display",
  subsets: ["latin"],
});

const monoFont = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "FI Infra Portfolio Console",
  description:
    "Portfolio dashboard for live positions and trade history backed by DuckDB.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${displayFont.variable} ${monoFont.variable} antialiased`}>
        <div className="page-background">
          <header className="sticky top-0 z-50 border-b border-white/6 bg-[rgba(5,10,18,0.78)] backdrop-blur-xl">
            <div className="mx-auto flex w-full max-w-[110rem] items-center justify-between px-6 py-5 md:px-8">
              <div className="flex items-center gap-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-cyan-400/30 bg-cyan-400/12 font-mono text-sm font-semibold tracking-[0.24em] text-cyan-300">
                  FI
                </div>
                <div className="flex flex-col">
                  <span className="text-xs uppercase tracking-[0.32em] text-[var(--broker-text-muted)]">
                    Broker Console
                  </span>
                  <span className="text-sm font-medium tracking-[0.18em] text-white">
                    FI INFRA
                  </span>
                </div>
              </div>

              <PlatformNav />
            </div>
          </header>

          {children}
        </div>
      </body>
    </html>
  );
}
