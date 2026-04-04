import { NextResponse } from "next/server";

// This page renders inside the OAuth popup and closes it
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const provider = searchParams.get("provider") || "";
  const error = searchParams.get("error") || "";

  // Return a small HTML page that posts a message to the opener and closes
  const html = `<!DOCTYPE html>
<html>
<head><title>Connected</title></head>
<body style="background:#0a0a0a;color:#fafafa;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
  <div style="text-align:center">
    <p>${error ? "Connection failed" : "Connected! Closing..."}</p>
  </div>
  <script>
    if (window.opener) {
      window.opener.postMessage({
        type: "pipedream-connect",
        provider: ${JSON.stringify(provider)},
        error: ${JSON.stringify(error)},
        success: ${!error}
      }, "*");
      setTimeout(() => window.close(), 500);
    } else {
      // Not in a popup — redirect to connect page
      window.location.href = "/connect?connected=${encodeURIComponent(provider)}";
    }
  </script>
</body>
</html>`;

  return new NextResponse(html, {
    headers: { "Content-Type": "text/html" },
  });
}
