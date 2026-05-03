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
    default: "MeetKai - Marketing OS Dashboard",
    template: "%s | MeetKai",
  },
  description: "Hosted dashboard for Kai Marketing OS: connect accounts, inspect audits, approve marketing actions, and track runs.",
  metadataBase: new URL("https://app.meetkai.xyz"),
  openGraph: {
    title: "MeetKai - Marketing OS Dashboard",
    description: "Connect accounts, inspect audits, approve proposed work, and track Kai Marketing OS runs.",
    url: "https://app.meetkai.xyz",
    siteName: "MeetKai",
    images: [{ url: "/images/kai-lean.png", width: 1024, height: 1024 }],
    type: "website",
  },
  twitter: {
    card: "summary",
    title: "MeetKai - Marketing OS Dashboard",
    description: "Hosted dashboard for Kai Marketing OS approvals, integrations, audits, and run history.",
  },
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      data-theme="light"
      className={`dark ${fraunces.variable} ${outfit.variable} ${jetbrains.variable}`}
      suppressHydrationWarning
    >
      <body className="min-h-screen font-body antialiased">
        {children}
      </body>
    </html>
  );
}
