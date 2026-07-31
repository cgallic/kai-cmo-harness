import type { Metadata } from "next";
import "./globals.css";

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
      className="dark"
      suppressHydrationWarning
    >
      <body className="min-h-screen font-body antialiased">
        {children}
      </body>
    </html>
  );
}
