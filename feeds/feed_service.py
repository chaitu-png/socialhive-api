"""
Feed Aggregation - Builds personalized news feeds.

BUG INVENTORY:
- BUG-040: N+1 query pattern in feed generation
- BUG-041: No caching - feed rebuilt from scratch every request
- BUG-042: Stale feed data served after new posts
"""

import time
from datetime import datetime
from typing import List, Dict, Optional
from collections import defaultdict


class FeedItem:
    def __init__(self, post_id: str, author_id: str, content: str,
                 timestamp: datetime):
        self.post_id = post_id
        self.author_id = author_id
        self.content = content
        self.timestamp = timestamp
        self.likes = 0
        self.comments_count = 0


class FeedService:
    """Generates personalized feeds for users."""

    def __init__(self):
        self.posts: Dict[str, FeedItem] = {}
        self.user_posts: Dict[str, List[str]] = defaultdict(list)
        self.follows: Dict[str, set] = defaultdict(set)

    def add_post(self, author_id: str, content: str) -> FeedItem:
        """Create a new post."""
        post_id = f"POST-{int(time.time() * 1000000)}"
        item = FeedItem(post_id, author_id, content, datetime.utcnow())
        self.posts[post_id] = item
        self.user_posts[author_id].append(post_id)
        return item

    def follow_user(self, follower_id: str, followed_id: str):
        """Add a follow relationship."""
        self.follows[follower_id].add(followed_id)

    def get_feed(self, user_id: str, page: int = 1,
                 page_size: int = 20) -> List[FeedItem]:
        """
        Generate personalized feed for a user.

        BUG-040: For each followed user, iterates ALL their posts.
        If user follows 1000 people with 1000 posts each,
        this iterates 1,000,000 items.

        BUG-041: No caching - entire feed rebuilt every call.
        BUG-042: No real-time updates - just sorts by timestamp.
        """
        followed = self.follows.get(user_id, set())
        all_items: List[FeedItem] = []

        # BUG-040: O(N*M) where N=followed users, M=posts per user
        for followed_id in followed:
            post_ids = self.user_posts.get(followed_id, [])
            for post_id in post_ids:  # BUG-040: Iterates ALL posts
                post = self.posts.get(post_id)
                if post:
                    all_items.append(post)

        # Sort all items by timestamp (expensive for large datasets)
        all_items.sort(key=lambda x: x.timestamp, reverse=True)

        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        return all_items[start:end]

    def like_post(self, post_id: str, user_id: str) -> bool:
        """Like a post. BUG: No deduplication - user can like multiple times."""
        post = self.posts.get(post_id)
        if not post:
            return False
        post.likes += 1  # BUG: No check if already liked
        return True

    def get_trending(self, limit: int = 10) -> List[FeedItem]:
        """Get trending posts by engagement."""
        all_posts = list(self.posts.values())
        # BUG: Sorts entire list for top-N (should use heap)
        all_posts.sort(key=lambda x: x.likes + x.comments_count, reverse=True)
        return all_posts[:limit]
