"use client";

import { useEffect, useState, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";
import type { Brand, Integration, Action, Audit, ChannelSnapshot } from "@/lib/types";
import type { RealtimePostgresChangesPayload } from "@supabase/supabase-js";

const supabase = createClient();

export function useBrand() {
  const [brand, setBrand] = useState<Brand | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetch() {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) { setLoading(false); return; }

      const { data } = await supabase
        .from("brands")
        .select("*")
        .eq("user_id", user.id)
        .limit(1)
        .single();

      setBrand(data);
      setLoading(false);
    }
    fetch();
  }, []);

  return { brand, loading };
}

export function useAudit(brandId: string | undefined) {
  const [audit, setAudit] = useState<Audit | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!brandId) { setLoading(false); return; }
    async function fetch() {
      const { data } = await supabase
        .from("audits")
        .select("*")
        .eq("brand_id", brandId)
        .order("created_at", { ascending: false })
        .limit(1)
        .single();
      setAudit(data);
      setLoading(false);
    }
    fetch();
  }, [brandId]);

  return { audit, loading };
}

export function useIntegrations(brandId: string | undefined) {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!brandId) { setLoading(false); return; }

    async function fetch() {
      const { data } = await supabase
        .from("integrations")
        .select("*")
        .eq("brand_id", brandId)
        .order("created_at", { ascending: true });
      setIntegrations(data || []);
      setLoading(false);
    }
    fetch();

    // Realtime subscription
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

    const { data } = await query;
    setActions(data || []);
    setLoading(false);
  }, [brandId, filters?.approval_state, filters?.execution_state]);

  useEffect(() => {
    fetchActions();

    if (!brandId) return;

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

  useEffect(() => {
    if (!brandId) { setLoading(false); return; }
    async function fetch() {
      let query = supabase
        .from("channel_snapshots")
        .select("*")
        .eq("brand_id", brandId)
        .order("created_at", { ascending: false });

      if (channel) {
        query = query.eq("channel", channel);
      }

      const { data } = await query.limit(10);
      setSnapshots(data || []);
      setLoading(false);
    }
    fetch();
  }, [brandId, channel]);

  return { snapshots, loading };
}
