export type YTItem = { videoId: string; title: string; channelTitle?: string; duration?: string };

export async function searchYoutube(
  productType: string,
  brand: string,
  model: string,
  keywords: string[]
): Promise<YTItem[]> {
  try {
    const response = await fetch('/api/youtube-search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        productType,
        brand,
        model,
        keywords,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to search YouTube videos');
    }

    const data = await response.json();
    const videos = data.videos || [];
    
    return videos.map((v: any) => ({
      videoId: v.videoId || v.video_id,
      title: v.title,
      channelTitle: v.channel || v.channelTitle || v.channel_title,
      duration: v.duration,
    }));
  } catch (error) {
    console.error('Error searching YouTube:', error);
    // Return empty array on error
    return [];
  }
}
