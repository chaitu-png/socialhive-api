
def get_user_feed(user_id, posts):
    # FIX: Use batch retrieval to avoid N+1 query problem
    author_ids = [p.author_id for p in posts]
    authors = db.get_users_bulk(author_ids)
    author_map = {a.id: a.name for a in authors}
    return [{"text": p.text, "author": author_map[p.author_id]} for p in posts]
