# Data Collection Module

The data collection module provides comprehensive tools for discovering, downloading, and managing HarmonyOS ArkTS repositories.

## Overview

This module handles the entire repository collection pipeline:
1. Repository discovery and metadata extraction
2. Batch downloading with parallel processing
3. Download failure recovery and repair
4. Progress tracking and logging

## Components

### Repository Discovery

#### `get_repo.py`
Discovers and collects metadata for HarmonyOS/ArkTS repositories.

**Features:**
- Searches multiple Git platforms (Gitee, GitHub)
- Extracts repository metadata (stars, forks, language)
- Filters repositories by relevance and quality
- Exports results to JSON format

**Usage:**
```bash
python get_repo.py
```

**Output:** `arkts_repos.json` - Repository metadata collection

### Repository Downloading

#### `download_repo.py`
Batch downloads repositories with advanced features.

**Features:**
- Parallel downloading (configurable worker count)
- Progress tracking with real-time updates
- Automatic retry with exponential backoff
- Shallow cloning for faster downloads
- Comprehensive error logging
- Chinese UI for better user experience

**Usage:**
```bash
python download_repo.py
```

**Configuration:**
- `max_workers`: Number of parallel download processes (default: 8)
- `max_retries`: Retry attempts per repository (default: 3)
- `timeout`: Download timeout in seconds (default: 300)

**Output:**
- `./newArktsRepos/` - Downloaded repositories
- `failed_repos.json` - Failed download log

### Repository Repair

#### `fix_incomplete_repos.py`
Repairs repositories with incomplete downloads.

**Problem Solved:**
Some repositories may have incomplete downloads due to network interruptions, resulting in directories with `.git` folders but missing working files.

**Features:**
- Automatic detection of incomplete repositories
- Batch repair with progress tracking
- Detailed repair logging
- Safe recovery using `git checkout`

**Usage:**
```bash
# Repair specific directory
python fix_incomplete_repos.py /path/to/repos

# Dry run (scan only)
python fix_incomplete_repos.py /path/to/repos --dry-run

# Custom log file
python fix_incomplete_repos.py /path/to/repos --log-file custom.json
```

#### `run_fix_repos.py`
Quick repair script for the default repository directory.

**Usage:**
```bash
python run_fix_repos.py
```

### Model Downloading

#### `download_hf_model.py`
Downloads pre-trained models from Hugging Face.

**Features:**
- Hugging Face model downloading
- Progress tracking
- Resume capability

#### `download_starcode.py`
Specialized downloader for StarCode models.

## Configuration Files

### `arkts_repos.json`
Repository metadata collection with the following structure:
```json
[
  {
    "name": "repository_name",
    "url": "git_clone_url",
    "stars": 123,
    "forks": 45,
    "language": "TypeScript",
    "description": "Repository description",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

### `failed_repos.json`
Failed download log with error details:
```json
{
  "failed_repos": [
    {
      "repo_name": "failed_repo",
      "error_code": 33024,
      "error_message": "Network timeout",
      "repo_info": {...}
    }
  ],
  "summary": {
    "total_failed": 56,
    "error_types": {...}
  }
}
```

## Common Issues and Solutions

### Network Issues
**Problem:** TLS handshake failures, connection timeouts

**Solutions:**
1. Configure Git for better network handling:
   ```bash
   git config --global http.postBuffer 524288000
   git config --global core.compression 0
   git config --global http.lowSpeedLimit 1000
   git config --global http.lowSpeedTime 300
   ```

2. Reduce parallel workers:
   ```python
   download_repo(repo_list, "./repos", max_workers=4)
   ```

3. Use SSH instead of HTTPS (if available)

### Incomplete Downloads
**Problem:** Repositories with `.git` folders but missing files

**Solution:** Use the repair tools:
```bash
python run_fix_repos.py
```

### Rate Limiting
**Problem:** API rate limits from Git platforms

**Solutions:**
1. Reduce download concurrency
2. Add delays between requests
3. Use authentication tokens (if available)

## Performance Optimization

### Download Speed
- Use shallow cloning (`--depth 1`)
- Optimize worker count based on network capacity
- Enable Git compression settings

### Memory Usage
- Process repositories in batches
- Clean up temporary files regularly
- Monitor disk space during downloads

### Network Efficiency
- Use CDN mirrors when available
- Implement connection pooling
- Cache repository metadata

## Monitoring and Logging

### Progress Tracking
- Real-time progress bars with ETA
- Download speed monitoring
- Success/failure statistics

### Error Logging
- Detailed error messages with context
- Structured JSON logs for analysis
- Automatic retry logging

### Health Checks
- Repository integrity validation
- Download completeness verification
- Disk space monitoring

## Best Practices

1. **Pre-flight Checks:**
   - Verify network connectivity
   - Check available disk space
   - Validate repository URLs

2. **Download Strategy:**
   - Start with smaller repositories
   - Use appropriate worker counts
   - Monitor system resources

3. **Error Handling:**
   - Always check repair logs
   - Retry failed downloads during stable network periods
   - Keep backup of metadata files

4. **Maintenance:**
   - Regularly clean up incomplete downloads
   - Update repository metadata periodically
   - Monitor for new repositories