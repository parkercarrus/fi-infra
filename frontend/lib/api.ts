import { PlatformData } from "@/lib/types";

const API_BASE_URL =
  process.env.PORTFOLIO_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function getPlatformData(): Promise<PlatformData | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/platform`, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`Platform request failed with ${response.status}`);
    }

    return (await response.json()) as PlatformData;
  } catch (error) {
    console.error("Unable to load platform data", error);
    return null;
  }
}
