// Runtime config endpoint. Lets the Cloud Run service set the concierge API URL
// via the CONCIERGE_API env var without rebuilding the image. Falls back to the
// build-time NEXT_PUBLIC_CONCIERGE_API.
export const dynamic = "force-dynamic";

export async function GET() {
  return Response.json({
    apiBase:
      process.env.CONCIERGE_API ||
      process.env.NEXT_PUBLIC_CONCIERGE_API ||
      "",
  });
}
