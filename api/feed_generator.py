
def get_user_feed(user_id, posts):
    feed = []
    for post in posts:
        # BUG: N+1 Query - Fetching user metadata for every single post
        author = db.get_user(post.author_id)
        feed.append({"text": post.text, "author": author.name})
    return feed
