# Debugging and Log Capture

[← Back to Documentation](README.md)

## Overview

This guide covers essential debugging techniques and log capture for the Job Search Assistant.

## Log Capture Methods

### Background Log Capture (Recommended)

Run the application in the background and capture all output:

```bash
cd job_search_assistant
mkdir -p logs
APP_ENV=dev uv run streamlit run ui/app.py > logs/app_logs.txt 2>&1 &
```

**Access the app:** Open http://localhost:8501 in your browser

**View logs:**
```bash
# View recent logs
tail -20 logs/app_logs.txt

# Follow logs in real-time
tail -f logs/app_logs.txt

# Search for errors
grep -i "error\|warning\|exception" logs/app_logs.txt
```

### Real-time Log Viewing

See logs in terminal while saving to file:

```bash
mkdir -p logs
APP_ENV=dev uv run streamlit run ui/app.py 2>&1 | tee logs/app_logs.txt
```

### Different Log Levels

Log levels are controlled by the `APP_ENV` environment variable:

```bash
# Debug level (most verbose) - good for development
APP_ENV=dev uv run streamlit run ui/app.py > logs/debug_logs.txt 2>&1 &

# Warning and error only - good for staging
APP_ENV=stage uv run streamlit run ui/app.py > logs/warning_logs.txt 2>&1 &

# Production level (INFO)
APP_ENV=prod uv run streamlit run ui/app.py > logs/prod_logs.txt 2>&1 &
```

## Log Analysis

### Log Format

Logs follow this format: `TIMESTAMP COMPONENT [LEVEL] MESSAGE`

Example:
```
2025-08-21 16:28:21 src.agent.workflows.interview_prep [INFO] Starting interview preparation
```

### Essential Log Commands

```bash
# Find errors and exceptions
grep -i "error\|exception\|traceback" logs/app_logs.txt

# Show only application logs (filter Streamlit noise)
grep "src\." logs/app_logs.txt

# Monitor specific features
grep "interview_prep\|job_evaluation" logs/app_logs.txt
```

## Process Management

```bash
# Check if app is running
ps aux | grep streamlit

# Stop the application
pkill -f "streamlit run ui/app.py"

# Stop log monitoring
pkill -f "tail -f logs/app_logs.txt"
```

## Common Issues

### No Logs Generated
**Check if app started:**
```bash
ps aux | grep streamlit
ls -la logs/app_logs.txt
```

### LLM Issues ("Generated 0 questions")
**Check API setup:**
```bash
# Look for API errors
grep -i "api\|anthropic\|error" logs/app_logs.txt

# Verify environment variables
env | grep -i "anthropic\|google"
```

### Port Already in Use
**Find and stop conflicting process:**
```bash
lsof -i :8501
kill <process_id>

# Or use different port
APP_ENV=dev uv run streamlit run ui/app.py --server.port 8502
```

### PII Detection Warnings
**These are usually harmless** - the app will work with default PII detection settings.

## Quick Debugging

```bash
# Get maximum detail for debugging
APP_ENV=dev uv run streamlit run ui/app.py > logs/debug.txt 2>&1 &

# Focus on specific features
grep "interview_prep" logs/app_logs.txt > logs/interview_debug.txt
grep "job_evaluation" logs/app_logs.txt > logs/job_eval_debug.txt

# Clean up old logs
rm -f logs/*.txt
```

## Troubleshooting Checklist

1. **Check if app is running:** `ps aux | grep streamlit`
2. **Check logs exist:** `ls -la logs/app_logs.txt`
3. **Look for errors:** `grep -i error logs/app_logs.txt | tail -10`
4. **Verify API keys:** `env | grep -E "(ANTHROPIC|GOOGLE)_API_KEY"`
5. **Test app access:** `curl -s http://localhost:8501`

## Need More Help?

If issues persist:
- Gather error logs with timestamps
- Check the [Installation Guide](installation.md)
- Review [Local Development Guide](LOCAL_DEVELOPMENT.md)

---

**Happy debugging!** 🐛🔍
