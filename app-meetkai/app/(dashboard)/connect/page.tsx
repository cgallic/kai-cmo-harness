"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { useBrand, useIntegrations } from "@/lib/hooks";
import { PROVIDERS, CHANNEL_CATEGORIES, type ProviderConfig, type Integration } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { createClient } from "@/lib/supabase/client";
import {
  BarChart3, Search, MapPin, Globe, ShoppingBag,
  Facebook, Instagram, Linkedin, Music, Youtube,
  Mail, Send, Megaphone, Target, Link2, RefreshCw,
} from "lucide-react";

const iconMap: Record<string, typeof BarChart3> = {
  BarChart3, Search, MapPin, Globe, ShoppingBag,
  Facebook, Instagram, Linkedin, Music, Youtube,
  Mail, Send, Megaphone, Target,
};

export default function ConnectPage() {
  const { brand, loading: brandLoading } = useBrand();
  const { integrations, loading: intLoading } = useIntegrations(brand?.id);
  const searchParams = useSearchParams();

  // Handle OAuth success redirect — confirm the connection
  useEffect(() => {
    const connectedProvider = searchParams.get("connected");
    if (!connectedProvider || !brand) return;

    async function confirmConnection() {
      const res = await fetch("/api/connections/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ brand_id: brand!.id, provider: connectedProvider }),
      });
      if (res.ok) {
        // Clean URL
        window.history.replaceState({}, "", "/connect");
      }
    }
    confirmConnection();
  }, [searchParams, brand]);

  if (brandLoading || intLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => <Skeleton key={i} className="h-36" />)}
        </div>
      </div>
    );
  }

  if (!brand) {
    return (
      <div className="text-center py-20">
        <p className="text-text-secondary">Set up your business profile first.</p>
        <a href="/settings?onboarding=true" className="text-amber hover:underline text-sm mt-2 inline-block">
          Go to Settings
        </a>
      </div>
    );
  }

  // Group connected integrations by channel+provider for lookup
  const integrationMap = new Map<string, Integration>();
  integrations.forEach((i) => integrationMap.set(`${i.channel}:${i.provider}`, i));

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight">Connect Accounts</h1>
        <p className="text-text-secondary text-sm mt-1">
          Link your marketing platforms to unlock AI-powered insights and actions.
        </p>
      </div>

      {/* Progress */}
      <div className="card">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-text-secondary">Connection progress</span>
          <span className="text-sm font-mono text-amber">
            {integrations.filter((i) => i.status === "connected").length} / {PROVIDERS.length}
          </span>
        </div>
        <div className="h-2 bg-border rounded-full overflow-hidden">
          <div
            className="h-full bg-amber rounded-full transition-all duration-500"
            style={{
              width: `${(integrations.filter((i) => i.status === "connected").length / PROVIDERS.length) * 100}%`,
            }}
          />
        </div>
      </div>

      {/* Provider grid by category */}
      {Object.entries(CHANNEL_CATEGORIES).map(([category, channels]) => {
        const providers = PROVIDERS.filter((p) => channels.includes(p.channel));
        if (providers.length === 0) return null;

        return (
          <div key={category}>
            <h2 className="font-display text-lg font-semibold mb-4">{category}</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {providers.map((provider) => (
                <ProviderCard
                  key={`${provider.channel}:${provider.provider}`}
                  provider={provider}
                  integration={integrationMap.get(`${provider.channel}:${provider.provider}`)}
                  brandId={brand.id}
                />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function ProviderCard({
  provider,
  integration,
  brandId,
}: {
  provider: ProviderConfig;
  integration?: Integration;
  brandId: string;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const supabase = createClient();
  const Icon = iconMap[provider.icon] || Link2;
  const status = integration?.status || "not_connected";

  async function handleConnect() {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch("/api/connections/connect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          brand_id: brandId,
          channel: provider.channel,
          provider: provider.provider,
          app_slug: provider.appSlug,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.error || "Connection failed");
        setLoading(false);
        return;
      }

      // If we got a connect link, open OAuth popup
      if (data.connect_link_url) {
        const popup = window.open(
          data.connect_link_url,
          "pipedream-connect",
          "width=600,height=700,left=200,top=100"
        );

        // Listen for postMessage from the popup callback page
        const handler = async (event: MessageEvent) => {
          if (event.data?.type !== "pipedream-connect") return;
          window.removeEventListener("message", handler);

          if (event.data.success) {
            // Confirm the connection server-side
            const confirmRes = await fetch("/api/connections/confirm", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ brand_id: brandId, provider: provider.provider }),
            });
            const confirmData = await confirmRes.json();
            console.log("Confirm result:", confirmData);
            // Reload to show updated status
            window.location.reload();
            return;
          }
          setLoading(false);
        };
        window.addEventListener("message", handler);

        // Fallback: if popup closes without messaging
        const checkClosed = setInterval(() => {
          if (popup?.closed) {
            clearInterval(checkClosed);
            window.removeEventListener("message", handler);
            setLoading(false);
          }
        }, 1000);

        setTimeout(() => {
          clearInterval(checkClosed);
          window.removeEventListener("message", handler);
          setLoading(false);
        }, 120000);
      } else {
        setLoading(false);
      }
    } catch (err) {
      console.error("Connection error:", err);
      setError("Something went wrong");
      setLoading(false);
    }
  }

  async function handleDisconnect() {
    if (!integration) return;
    setLoading(true);
    await supabase
      .from("integrations")
      .update({ status: "disconnected", updated_at: new Date().toISOString() })
      .eq("id", integration.id);
    setLoading(false);
  }

  return (
    <Card className="flex flex-col">
      <div className="flex items-start gap-3 mb-4">
        <div className="w-10 h-10 rounded-lg bg-bg-elevated border border-border flex items-center justify-center flex-shrink-0">
          <Icon className="w-5 h-5 text-text-secondary" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold">{provider.name}</h3>
          <p className="text-xs text-text-tertiary capitalize">{provider.channel.replace(/_/g, " ")}</p>
        </div>
        {integration && <Badge status={integration.status} />}
      </div>

      {error && (
        <p className="text-error text-xs mb-2">{error}</p>
      )}

      <div className="mt-auto pt-2">
        {status === "connected" ? (
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" className="flex-1" disabled>
              <RefreshCw className="w-3.5 h-3.5" />
              Sync
            </Button>
            <Button variant="ghost" size="sm" onClick={handleDisconnect} loading={loading}>
              Disconnect
            </Button>
          </div>
        ) : (
          <Button
            variant={status === "not_connected" ? "primary" : "secondary"}
            size="sm"
            className="w-full"
            onClick={handleConnect}
            loading={loading}
          >
            {status === "pending_auth" ? "Continue Setup" : status === "degraded" ? "Reconnect" : "Connect"}
          </Button>
        )}
      </div>
    </Card>
  );
}
