import git
import os

def get_deck_repo(deck_path):
    """Initializes and returns a Git Repo object for a specific deck path if it's a repo."""
    if os.path.exists(os.path.join(deck_path, ".git")):
        return git.Repo(deck_path)
    return None

def get_branches(deck_path):
    """Returns branches for a specific deck repository."""
    repo = get_deck_repo(deck_path)
    if not repo:
        return ["main"] # Fallback if not a git repo yet
    return [branch.name for branch in repo.branches]

def checkout_branch(deck_path, branch_name):
    """Checks out a branch for a specific deck repository."""
    repo = get_deck_repo(deck_path)
    if not repo:
        return "Not a Git repository."
    
    if repo.is_dirty():
        return "Warning: Uncommitted changes in this deck!"
    
    try:
        repo.git.checkout(branch_name)
        return f"Checked out branch: {branch_name}"
    except Exception as e:
        return f"Error checking out branch: {str(e)}"

def get_active_branch(deck_path):
    """Gets the currently active branch name for a deck."""
    repo = get_deck_repo(deck_path)
    if not repo:
        return "unknown"
    return repo.active_branch.name


def create_branch(deck_path, branch_name):
    """Creates a new branch and checks it out."""
    repo = get_deck_repo(deck_path)
    if not repo:
        return "Not a Git repository."
    
    try:
        # Create and checkout the new branch
        new_branch = repo.create_head(branch_name)
        repo.head.reference = new_branch
        repo.head.reset(index=True, working_tree=True)
        return f"Created and switched to new branch: {branch_name}"
    except Exception as e:
        return f"Error creating branch: {str(e)}"

def commit_changes(deck_path, commit_message):
    """Stages all changes in the deck repo and commits them."""
    repo = get_deck_repo(deck_path)
    if not repo:
        return "Not a Git repository."
    
    if not repo.is_dirty(untracked_files=True):
        return "No changes to commit."
    
    try:
        # Stage all changes (including new untracked files)
        repo.git.add(A=True)
        # Commit
        repo.index.commit(commit_message or "Update deck")
        return f"Successfully committed: '{commit_message}'"
    except Exception as e:
        return f"Error committing: {str(e)}"