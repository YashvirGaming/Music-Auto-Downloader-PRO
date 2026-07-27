class YouTubeSearcher:
    @staticmethod
    def build_query(artist: str, limit: int, official_only: bool) -> str:
        # Request extra search results to allow for Shorts filtering
        fetch_limit = limit * 2
        if official_only:
            return f"ytsearch{fetch_limit}:{artist} official topic"
        return f"ytsearch{fetch_limit}:{artist}"