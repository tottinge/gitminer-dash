import git


def get_most_recent_tags(repo: git.Repo, desired: int):
    if desired <= 0:
        return []
    return sorted(repo.tags, key=lambda tag: tag.commit.authored_datetime)[-desired:]
