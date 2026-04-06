"use client";

import { useRouter } from "next/navigation";
import { FileText, Calendar, Search, Megaphone, Mail, Users } from "lucide-react";

const quickActions = [
  { label: "Write Content", icon: FileText, description: "Blog, email, social, ads", href: "/content?action=write" },
  { label: "Plan Calendar", icon: Calendar, description: "Monthly content calendar", href: "/content?action=calendar" },
  { label: "Audit Page", icon: Search, description: "CRO or SEO audit", href: "/analytics" },
  { label: "Run Ads", icon: Megaphone, description: "Ad campaign copy", href: "/content?action=ads" },
  { label: "Cold Outreach", icon: Mail, description: "Email sequences", href: "/content?action=outreach" },
  { label: "Competitor Intel", icon: Users, description: "Competitive analysis", href: "/content?action=competitors" },
];

export function QuickActions() {
  const router = useRouter();

  return (
    <div className="card">
      <h3 className="section-title mb-4">Quick Actions</h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {quickActions.map((action) => {
          const Icon = action.icon;
          return (
            <button
              key={action.label}
              onClick={() => router.push(action.href)}
              className="flex flex-col items-center gap-2 p-4 rounded-lg bg-bg-elevated border border-border hover:border-amber/30 hover:bg-amber-dim/30 transition-colors text-center"
            >
              <Icon className="w-5 h-5 text-amber" />
              <div>
                <p className="text-sm font-medium">{action.label}</p>
                <p className="text-[10px] text-text-tertiary">{action.description}</p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
