"use client";

import { useEffect, useState, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";
import type { Brand, Integration, Action, Audit, ChannelSnapshot, Content, AgentRun } from "@/lib/types";
import type { RealtimePostgresChangesPayload } from "@supabase/supabase-js";

export function useBrand() {
  const [brand, setBrand] = useState<Brand | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    const supabase = createClient();
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) { setLoading(false); return; }

    const { data: rows, error } = await supabase
      .from("brands")
      .select("*")
      .eq("user_id", user.id)
      .order("created_at", { ascending: false })
      .limit(1);

    if (error) {
      console.error("useBrand error:", error.message);
      setBrand(null);
    } else {
      setBrand(rows?.[0] ?? null);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { brand, loading, refresh };
}

export function useAudit(brandId: string | undefined) {
  const [audit, setAudit] = useState<Audit | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchAudit = useCallback(async () => {
    if (!brandId) { setLoading(false); return; }
    const supabase = createClient();
    const { data: rows, error } = await supabase
      .from("audits")
      .select("*")
      .eq("brand_id", brandId)
      .order("created_at", { ascending: false })
      .limit(1);

    if (error) {
      console.error("useAudit error:", error.message);
      setAudit(null);
    } else {
      setAudit(rows?.[0] ?? null);
    }
    setLoading(false);
  }, [brandId]);

  useEffect(() => {
    fetchAudit();
  }, [fetchAudit]);

  return { audit, loading, setAudit, refresh: fetchAudit };
}

export function useIntegrations(brandId: string | undefined) {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!brandId) { setLoading(false); return; }

    async function fetch() {
      const supabase = createClient();
      const { data, error } = await supabase
        .from("integrations")
        .select("*")
        .eq("brand_id", brandId)
        .order("created_at", { ascending: true });
      if (error) {
        console.error("useIntegrations error:", error.message);
      }
      setIntegrations(data || []);
      setLoading(false);
    }
    fetch();

    // Realtime subscription
    const supabase = createClient();
    const channel = supabase
      .channel("integrations-changes")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "integrations", filter: `brand_id=eq.${brandId}` },
        (payload: RealtimePostgresChangesPayload<Integration>) => {
          if (payload.eventType === "INSERT") {
            setIntegrations((prev) => [...prev, payload.new as Integration]);
          } else if (payload.eventType === "UPDATE") {
            setIntegrations((prev) =>
              prev.map((i) => (i.id === (payload.new as Integration).id ? (payload.new as Integration) : i))
            );
          } else if (payload.eventType === "DELETE") {
            setIntegrations((prev) => prev.filter((i) => i.id !== (payload.old as Integration).id));
          }
        }
      )
      .subscribe();

    return () => { supabase.removeChannel(channel); };
  }, [brandId]);

  return { integrations, loading };
}

export function useActions(brandId: string | undefined, filters?: { approval_state?: string; execution_state?: string }) {
  const [actions, setActions] = useState<Action[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchActions = useCallback(async () => {
    if (!brandId) { setLoading(false); return; }

    const supabase = createClient();
    let query = supabase
      .from("actions")
      .select("*")
      .eq("brand_id", brandId)
      .order("created_at", { ascending: false })
      .limit(50);

    if (filters?.approval_state) {
      query = query.eq("approval_state", filters.approval_state);
    }
    if (filters?.execution_state) {
      query = query.eq("execution_state", filters.execution_state);
    }

    const { data, error } = await query;
    if (error) {
      console.error("useActions error:", error.message);
    }
    setActions(data || []);
    setLoading(false);
  }, [brandId, filters?.approval_state, filters?.execution_state]);

  useEffect(() => {
    fetchActions();

    if (!brandId) return;

    const supabase = createClient();
    const channel = supabase
      .channel("actions-changes")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "actions", filter: `brand_id=eq.${brandId}` },
        () => { fetchActions(); }
      )
      .subscribe();

    return () => { supabase.removeChannel(channel); };
  }, [brandId, fetchActions]);

  return { actions, loading, refresh: fetchActions };
}

export function useSnapshots(brandId: string | undefined, channel?: string) {
  const [snapshots, setSnapshots] = useState<ChannelSnapshot[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    if (!brandId) { setLoading(false); return; }

    const supabase = createClient();
    let query = supabase
      .from("channel_snapshots")
      .select("*")
      .eq("brand_id", brandId)
      .order("created_at", { ascending: false });

    if (channel) {
      query = query.eq("channel", channel);
    }

    const { data, error } = await query.limit(50);
    if (error) {
      console.error("useSnapshots error:", error.message);
    }
    setSnapshots(data || []);
    setLoading(false);
  }, [brandId, channel]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { snapshots, loading, refresh };
}

export function useContent(brandId: string | undefined, filters?: { status?: string; format?: string }) {
  const [content, setContent] = useState<Content[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchContent = useCallback(async () => {
    if (!brandId) { setLoading(false); return; }

    const supabase = createClient();
    let query = supabase
      .from("content")
      .select("*")
      .eq("brand_id", brandId)
      .order("created_at", { ascending: false })
      .limit(50);

    if (filters?.status) query = query.eq("status", filters.status);
    if (filters?.format) query = query.eq("format", filters.format);

    const { data, error } = await query;
    if (error) console.error("useContent error:", error.message);
    setContent(data || []);
    setLoading(false);
  }, [brandId, filters?.status, filters?.format]);

  useEffect(() => {
    fetchContent();

    if (!brandId) return;

    const supabase = createClient();
    const channel = supabase
      .channel("content-changes")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "content", filter: `brand_id=eq.${brandId}` },
        () => { fetchContent(); }
      )
      .subscribe();

    return () => { supabase.removeChannel(channel); };
  }, [brandId, fetchContent]);

  return { content, loading, refresh: fetchContent };
}

export function useAgentRuns(brandId: string | undefined) {
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchRuns = useCallback(async () => {
    if (!brandId) { setLoading(false); return; }

    const supabase = createClient();
    const { data, error } = await supabase
      .from("agent_runs")
      .select("*")
      .eq("brand_id", brandId)
      .order("created_at", { ascending: false })
      .limit(20);

    if (error) console.error("useAgentRuns error:", error.message);
    setRuns(data || []);
    setLoading(false);
  }, [brandId]);

  useEffect(() => {
    fetchRuns();

    if (!brandId) return;

    const supabase = createClient();
    const channel = supabase
      .channel("agent-runs-changes")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "agent_runs", filter: `brand_id=eq.${brandId}` },
        () => { fetchRuns(); }
      )
      .subscribe();

    return () => { supabase.removeChannel(channel); };
  }, [brandId, fetchRuns]);

  return { runs, loading, refresh: fetchRuns };
}
