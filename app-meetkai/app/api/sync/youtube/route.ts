import { createClient, createServiceClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";
import { PipedreamClient } from "@pipedream/sdk";

function getPd() {
  return new PipedreamClient({
    projectId: process.env.PIPEDREAM_PROJECT_ID!,
    projectEnvironment:
      (process.env.PIPEDREAM_ENVIRONMENT as "development" | "production") || "development",
    clientId: process.env.PIPEDREAM_CLIENT_ID!,
    clientSecret: process.env.PIPEDREAM_CLIENT_SECRET!,
  });
}

interface YtChannelItem {
  snippet: { title: string };
  statistics: {
    subscriberCount: string;
    viewCount: string;
    videoCount: string;
  };
  contentDetails?: {
    relatedPlaylists?: { uploads?: string };
  };
}

interface YtChannelResponse {
  items?: YtChannelItem[];
}

interface YtSearchItem {
  id: { videoId: string };
  snippet: { title: string; publishedAt: string };
}

interface YtSearchResponse {
  items?: YtSearchItem[];
}

interface YtVideoStatistics {
  viewCount: string;
  likeCount: string;
  commentCount: string;
}

interface YtVideoItem {
  id: string;
  statistics: YtVideoStatistics;
}

interface YtVideosResponse {
  items?: YtVideoItem[];
}

export async function POST(request: Request) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { brand_id } = await request.json();

  const { data: brand } = await supabase
    .from("brands")
    .select("id")
    .eq("id", brand_id)
    .eq("user_id", user.id)
    .single();

  if (!brand) {
    return NextResponse.json({ error: "Brand not found" }, { status: 404 });
  }

  const serviceClient = await createServiceClient();

  const { data: integrations } = await serviceClient
    .from("integrations")
    .select("*")
    .eq("brand_id", brand_id)
    .eq("provider", "youtube")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0) {
    return NextResponse.json({ error: "YouTube not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const integration = integrations[0];
  if (!integration.connected_account_id) {
    return NextResponse.json({ error: "YouTube not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const accountId = integration.connected_account_id;

  try {
    const pd = getPd();

    // Fetch channel info (stats, snippet, content details)
    const channelRes = await pd.proxy.get({
      url: "https://www.googleapis.com/youtube/v3/channels?part=statistics,snippet,contentDetails&mine=true",
      accountId,
      externalUserId: brand_id,
    });

    const channelData = ((channelRes as { data?: YtChannelResponse })?.data ?? channelRes) as YtChannelResponse;
    const channel = channelData?.items?.[0];

    if (!channel) {
      return NextResponse.json({ error: "No YouTube channel found", code: "NO_CHANNEL" }, { status: 404 });
    }

    const channelTitle = channel.snippet.title;
    const subscribers = parseInt(channel.statistics.subscriberCount || "0");
    const totalViews = parseInt(channel.statistics.viewCount || "0");
    const videoCount = parseInt(channel.statistics.videoCount || "0");

    // Fetch recent videos (last 10)
    const searchRes = await pd.proxy.get({
      url: "https://www.googleapis.com/youtube/v3/search?part=snippet&forMine=true&type=video&maxResults=10&order=date",
      accountId,
      externalUserId: brand_id,
    });

    const searchData = ((searchRes as { data?: YtSearchResponse })?.data ?? searchRes) as YtSearchResponse;
    const searchItems = searchData?.items || [];

    let recentVideos: { title: string; views: number; likes: number; comments: number; published_at: string }[] = [];

    if (searchItems.length > 0) {
      const videoIds = searchItems.map((item) => item.id.videoId).join(",");

      // Fetch stats for those videos
      const videosRes = await pd.proxy.get({
        url: `https://www.googleapis.com/youtube/v3/videos?part=statistics&id=${videoIds}`,
        accountId,
        externalUserId: brand_id,
      });

      const videosData = ((videosRes as { data?: YtVideosResponse })?.data ?? videosRes) as YtVideosResponse;
      const videoItems = videosData?.items || [];

      // Build a stats lookup by video ID
      const statsMap = new Map<string, YtVideoStatistics>();
      for (const v of videoItems) {
        statsMap.set(v.id, v.statistics);
      }

      recentVideos = searchItems.map((item) => {
        const stats = statsMap.get(item.id.videoId);
        return {
          title: item.snippet.title,
          views: parseInt(stats?.viewCount || "0"),
          likes: parseInt(stats?.likeCount || "0"),
          comments: parseInt(stats?.commentCount || "0"),
          published_at: item.snippet.publishedAt,
        };
      });
    }

    const snapshot = {
      channel_title: channelTitle,
      subscribers,
      total_views: totalViews,
      video_count: videoCount,
      recent_videos: recentVideos,
    };

    await serviceClient.from("channel_snapshots").insert({
      brand_id,
      channel: "social",
      provider: "youtube",
      snapshot_data: snapshot,
    });

    await serviceClient
      .from("integrations")
      .update({ last_sync_at: new Date().toISOString() })
      .eq("id", integration.id);

    return NextResponse.json({ status: "synced", data: snapshot });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("YouTube sync error:", message);
    return NextResponse.json({ error: "Sync failed", code: "SYNC_FAILED", detail: message }, { status: 500 });
  }
}
