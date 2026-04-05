import type { Metadata } from "next";
import { Fraunces, Outfit, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
  display: "swap",
  weight: ["400", "500", "600", "700", "800", "900"],
});

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
  display: "swap",
  weight: ["300", "400", "500", "600", "700"],
});

const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  display: "swap",
  weight: ["400", "500", "700"],
});

export const metadata: Metadata = {
  title: {
    default: "MeetKai Dashboard",
    template: "%s | MeetKai",
  },
  description: "AI CMO Dashboard — connect your marketing accounts, see what AI finds, approve actions.",
  metadataBase: new URL("https://app.meetkai.xyz"),
  openGraph: {
    title: "MeetKai — AI CMO Dashboard",
    description: "Connect your marketing accounts. Get AI-powered audits. Approve actions with one click.",
    url: "https://app.meetkai.xyz",
    siteName: "MeetKai",
    images: [{ url: "/logo.svg", width: 160, height: 40 }],
    type: "website",
  },
  twitter: {
    card: "summary",
    title: "MeetKai — AI CMO Dashboard",
    description: "Connect your marketing accounts. Get AI-powered audits. Approve actions with one click.",
  },
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`dark ${fraunces.variable} ${outfit.variable} ${jetbrains.variable}`}>
      <body className="min-h-screen font-body antialiased">
        {children}
      </body>
    </html>
  );
}
