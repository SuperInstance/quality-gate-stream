"""
PLATO Room: modelexperiment
Tile: **3. Function 2: `git_repo_health`**
Domain: modelexperiment
"""

import subprocess
import os

def git_repo_health(repo_path):
    """
    Check health of a git repository.
    
    Returns dict with uncommitted changes count, unpushed commits,
    branch divergence status, and summary string.
    """
    result = {
        'has_uncommitted': False,
        'unpushed_commits': 0,
        'branch_diverged': False,
        'status_summary': 'unknown'
    }
    
    if not os.path.exists(os.path.join(repo_path, '.git')):
        result['status_summary'] = 'not_a_git_repo'
        return result
    
    try:
        # Check for uncommitted changes
        status_proc = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        result['has_uncommitted'] = len(status_proc.stdout.strip()) > 0
        
        # Check unpushed commits (compare local vs origin)
        log_proc = subprocess.run(
            ['git', 'log', '--oneline', 'origin/HEAD..HEAD'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        result['unpushed_commits'] = len(log_proc.stdout.strip().splitlines()) if log_proc.stdout else 0
        
        # Check branch divergence
        rev_list_proc = subprocess.run(
            ['git', 'rev-list', '--left-right', 'HEAD...origin/HEAD', '--count'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        if rev_list_proc.stdout:
            left, right = map(int, rev_list_proc.stdout.strip().split())
            result['branch_diverged'] = left > 0 or right > 0
        
        # Generate summary
        if result['has_uncommitted']:
            result['status_summary'] = 'dirty'
        elif result['unpushed_commits'] > 0:
            result['status_summary'] = 'unpushed'
        elif result['branch_diverged']:
            result['status_summary'] = 'diverged'
        else:
            result['status_summary'] = 'clean'
            
    except (subprocess.SubprocessError, FileNotFoundError, ValueError) as e:
        result['status_summary'] = f'error: {str(e)}'
    
    return result

