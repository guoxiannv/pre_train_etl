# Repository Repair Guide

This guide covers the repository repair tools designed to fix incomplete Git repository downloads that may occur during the data collection process.

## Problem Overview

### What Are Incomplete Repositories?

During the repository download process, network interruptions, timeouts, or other issues can result in "incomplete" repositories. These repositories have the following characteristics:

- Contains a complete `.git` directory with commit history
- Missing working directory files (source code, documentation, etc.)
- `git status` shows all files as "deleted"
- Directory appears empty except for the `.git` folder

### Common Causes

1. **Network Interruptions**: Connection drops during file checkout
2. **Timeout Issues**: Download timeout during the working tree population
3. **Disk Space**: Insufficient disk space during file extraction
4. **Permission Issues**: File system permission problems
5. **Git Errors**: Git internal errors during checkout process

## Repair Tools

### Main Repair Script

#### `fix_incomplete_repos.py`
Comprehensive repository repair tool with advanced features.

**Features:**
- Automatic detection of incomplete repositories
- Batch processing with progress tracking
- Detailed logging and reporting
- Safe recovery using Git commands
- Configurable repair strategies

**Usage:**
```bash
# Repair repositories in specific directory
python fix_incomplete_repos.py /path/to/repositories

# Dry run (scan only, no repairs)
python fix_incomplete_repos.py /path/to/repositories --dry-run

# Custom log file
python fix_incomplete_repos.py /path/to/repositories --log-file repair_log.json
```

**Command Line Options:**
- `repos_path`: Path to the directory containing repositories
- `--log-file`: Custom log file name (default: fix_repos.json)
- `--dry-run`: Scan for issues without performing repairs

### Quick Repair Script

#### `run_fix_repos.py`
Simplified repair script for the default repository directory.

**Features:**
- One-click repair for `newArktsRepos` directory
- Automatic configuration
- User-friendly output
- Quick status summary

**Usage:**
```bash
python run_fix_repos.py
```

## Repair Process

### Detection Phase

1. **Directory Scanning**: Scan all subdirectories in the target path
2. **Git Repository Check**: Verify presence of `.git` directory
3. **Working Tree Check**: Check for files outside `.git` directory
4. **Status Classification**: Classify repositories as:
   - `complete`: Has both `.git` and working files
   - `incomplete`: Has `.git` but missing working files
   - `invalid`: Missing `.git` directory
   - `empty`: Empty directory

### Repair Phase

1. **Commit History Verification**: Check if repository has commit history
2. **Working Tree Recovery**: Execute `git checkout HEAD -- .`
3. **Verification**: Confirm files are restored
4. **Status Update**: Update repair status and logs

### Recovery Algorithm

```python
def fix_incomplete_repo(repo_path):
    try:
        # Change to repository directory
        os.chdir(repo_path)
        
        # Verify commit history exists
        result = subprocess.run(['git', 'log', '--oneline', '-1'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            return False, "No commit history"
        
        # Restore working directory files
        result = subprocess.run(['git', 'checkout', 'HEAD', '--', '.'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            return True, "Repair successful"
        else:
            return False, f"Repair failed: {result.stderr}"
            
    except Exception as e:
        return False, f"Error during repair: {str(e)}"
```

## Output and Logging

### Console Output

```
Starting repair for newArktsRepos directory...
==================================================
Scanned 2291 repository directories

Scanning repository status...
Scanning repositories: 100%|████████████| 2291/2291 [00:00<00:00, 99560.18it/s]

Scan Results:
  Complete repositories: 2289
  Incomplete repositories: 2
  Invalid repositories: 0
  Empty directories: 0

Starting repair of 2 incomplete repositories...
Repairing repositories: 100%|██████████| 2/2 [00:01<00:00,  1.53it/s]

Repair completed!
  Successfully repaired: 1
  Repair failed: 1
  Repair log saved to: fix_repos_log.json

✅ Successfully repaired 1 repository!
```

### Log File Format

The repair process generates detailed JSON logs:

```json
{
  "scan_time": "/home/user/project",
  "base_path": "newArktsRepos",
  "incomplete_repos": [
    {
      "name": "repository_name",
      "path": "path/to/repository",
      "status": "incomplete",
      "fix_result": {
        "success": true,
        "message": "Repair successful"
      }
    }
  ],
  "fixed_repos": [...],
  "failed_fixes": [...]
}
```

### Statistics Summary

```python
stats = {
    'total': 2291,           # Total repositories scanned
    'complete': 2289,        # Already complete repositories
    'incomplete': 2,         # Incomplete repositories found
    'invalid': 0,            # Invalid repositories
    'empty': 0,              # Empty directories
    'fixed': 1,              # Successfully repaired
    'fix_failed': 1          # Failed repairs
}
```

## Repair Strategies

### Standard Repair
Uses `git checkout HEAD -- .` to restore all files from the latest commit.

**Advantages:**
- Safe and reliable
- Preserves all file permissions
- Handles binary files correctly
- Fast execution

**Limitations:**
- Requires valid commit history
- Cannot fix corrupted Git repositories

### Alternative Strategies

#### Reset-based Repair
```bash
git reset --hard HEAD
```

**Use Case**: When checkout fails but reset might work

#### Branch-specific Repair
```bash
git checkout main -- .
```

**Use Case**: When HEAD is detached or corrupted

#### Selective Repair
```bash
git checkout HEAD -- src/
git checkout HEAD -- docs/
```

**Use Case**: When only specific directories need repair

## Error Handling

### Common Failure Scenarios

#### No Commit History
**Error**: "No commit history"
**Cause**: Repository was initialized but never had commits
**Solution**: Repository cannot be repaired, consider re-downloading

#### Corrupted Git Repository
**Error**: "fatal: not a git repository"
**Cause**: `.git` directory is corrupted
**Solution**: Delete and re-download repository

#### Permission Issues
**Error**: "Permission denied"
**Cause**: Insufficient file system permissions
**Solution**: Check and fix directory permissions

#### Disk Space Issues
**Error**: "No space left on device"
**Cause**: Insufficient disk space
**Solution**: Free up disk space before repair

### Error Recovery

```python
def handle_repair_error(repo_path, error_message):
    if "No commit history" in error_message:
        # Mark for re-download
        mark_for_redownload(repo_path)
    elif "Permission denied" in error_message:
        # Attempt permission fix
        fix_permissions(repo_path)
    elif "not a git repository" in error_message:
        # Mark as corrupted
        mark_as_corrupted(repo_path)
    else:
        # Log for manual investigation
        log_manual_review(repo_path, error_message)
```

## Best Practices

### Pre-repair Checks

1. **Backup Important Data**: Backup any custom modifications
2. **Check Disk Space**: Ensure sufficient space for file restoration
3. **Verify Permissions**: Check read/write permissions
4. **Network Stability**: Ensure stable network for any remote operations

### During Repair

1. **Monitor Progress**: Watch for error patterns
2. **Resource Usage**: Monitor CPU and memory usage
3. **Log Analysis**: Review logs for recurring issues
4. **Interrupt Handling**: Allow safe interruption if needed

### Post-repair Validation

1. **File Count Verification**: Check if expected files are present
2. **Repository Integrity**: Verify Git repository integrity
3. **Content Validation**: Spot-check file contents
4. **Size Comparison**: Compare with expected repository sizes

## Performance Considerations

### Optimization Strategies

#### Parallel Processing
```python
from multiprocessing import Pool

def repair_repositories_parallel(repo_list, max_workers=4):
    with Pool(max_workers) as pool:
        results = pool.map(fix_incomplete_repo, repo_list)
    return results
```

#### Batch Processing
```python
def repair_in_batches(repo_list, batch_size=100):
    for i in range(0, len(repo_list), batch_size):
        batch = repo_list[i:i+batch_size]
        repair_batch(batch)
```

#### Memory Management
- Process repositories one at a time
- Clear temporary variables
- Use generators for large lists
- Monitor memory usage

### Performance Metrics

```python
performance_stats = {
    'repositories_per_minute': 150,
    'average_repair_time': '2.5 seconds',
    'memory_usage': '50 MB peak',
    'success_rate': '95%'
}
```

## Monitoring and Maintenance

### Health Checks

#### Repository Integrity Check
```bash
# Verify Git repository integrity
git fsck --full

# Check for missing objects
git count-objects -v
```

#### Automated Monitoring
```python
def monitor_repository_health(repo_path):
    checks = {
        'git_integrity': check_git_integrity(repo_path),
        'file_completeness': check_file_completeness(repo_path),
        'size_consistency': check_size_consistency(repo_path)
    }
    return checks
```

### Preventive Measures

1. **Regular Scans**: Schedule periodic repository health checks
2. **Download Monitoring**: Monitor download success rates
3. **Storage Monitoring**: Track disk space usage
4. **Network Quality**: Monitor network stability during downloads

### Maintenance Tasks

1. **Log Rotation**: Rotate and archive repair logs
2. **Cleanup**: Remove temporary files and failed downloads
3. **Statistics**: Generate repair success statistics
4. **Updates**: Keep repair tools updated

## Integration

### With Download Pipeline

```python
# Integrate repair into download workflow
def download_with_repair(repo_list):
    # Download repositories
    download_results = download_repositories(repo_list)
    
    # Repair incomplete downloads
    repair_results = repair_incomplete_repos()
    
    # Combine results
    return combine_results(download_results, repair_results)
```

### With CI/CD

```yaml
# GitHub Actions example
name: Repository Maintenance
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  repair:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run repository repair
        run: python data_collection/run_fix_repos.py
```

### With Monitoring Systems

```python
# Prometheus metrics example
from prometheus_client import Counter, Histogram

repair_counter = Counter('repos_repaired_total', 'Total repaired repositories')
repair_duration = Histogram('repair_duration_seconds', 'Repair duration')

def repair_with_metrics(repo_path):
    with repair_duration.time():
        success, message = fix_incomplete_repo(repo_path)
        if success:
            repair_counter.inc()
    return success, message
```