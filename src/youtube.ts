export type YTItem = { videoId: string; title: string; channelTitle?: string; duration?: string };

const CURATED: YTItem[] = [
  { videoId: 'xQZ8dS2o3kI', title: 'Basic troubleshooting checklist' },
  { videoId: 'Qp7R8s1V2xY', title: 'How to fix common device issues' },
  { videoId: 'Hk9L2d3S4mN', title: 'Repair and diagnosis guide' },
];

export async function searchYoutube(q: string): Promise<YTItem[]> {
  try {
    // Use Vite env convention; fallback to undefined when building outside Vite
    const apiKey = (import.meta as any)?.env?.VITE_YOUTUBE_API_KEY as string | undefined;
    if (!apiKey) return CURATED;

    const searchUrl = new URL('https://www.googleapis.com/youtube/v3/search');
    searchUrl.searchParams.set('part', 'snippet');
    searchUrl.searchParams.set('q', q);
    searchUrl.searchParams.set('type', 'video');
    searchUrl.searchParams.set('maxResults', '5');
    searchUrl.searchParams.set('safeSearch', 'moderate');
    searchUrl.searchParams.set('key', apiKey);

    const s = await fetch(searchUrl.toString());
    if (!s.ok) throw new Error('search failed');
    const sJson = await s.json();
    const ids = (sJson.items || [])
      .map((it: any) => it?.id?.videoId)
      .filter((v: string) => !!v);

    if (!ids.length) return CURATED;

    const videosUrl = new URL('https://www.googleapis.com/youtube/v3/videos');
    videosUrl.searchParams.set('part', 'contentDetails,snippet');
    videosUrl.searchParams.set('id', ids.join(','));
    videosUrl.searchParams.set('key', apiKey);

    const v = await fetch(videosUrl.toString());
    if (!v.ok) throw new Error('videos failed');
    const vJson = await v.json();

    const items: YTItem[] = (vJson.items || []).map((it: any) => ({
      videoId: it.id,
      title: it.snippet?.title ?? 'Tutorial',
      channelTitle: it.snippet?.channelTitle,
      duration: it.contentDetails?.duration,
    }));

    // Rerank: prioritize titles with troubleshoot/repair/fix and device terms
    const lowerQ = q.toLowerCase();
    const positive = ['troubleshoot', 'repair', 'fix', 'how to', 'guide', 'tutorial'];
    const negative = ['lyrics', 'music', 'song', 'remix', 'cover'];

    const score = (t: string) => {
      const L = t.toLowerCase();
      let s = 0;
      for (const p of positive) if (L.includes(p)) s += 3;
      for (const term of lowerQ.split(/\s+/)) if (term.length > 3 && L.includes(term)) s += 1;
      for (const n of negative) if (L.includes(n)) s -= 5;
      return s;
    };

    const ranked = items.sort((a, b) => score(b.title) - score(a.title)).slice(0, 3);
    return ranked.length ? ranked : CURATED;
  } catch {
    return CURATED;
  }
}
