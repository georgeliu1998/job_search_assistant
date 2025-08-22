# Debugging and Log Capture

[← Back to Documentation](README.md)

## Overview

This guide covers debugging techniques, log capture methods, and troubleshooting runtime issues with the Job Search Assistant.

## Log Capture Methods

### Method 1: Background Execution with Full Log Capture (Recommended)

Run the application in the background and capture all output to a file:

```bash
cd job_search_assistant
mkdir -p logs
uv run streamlit run ui/app.py > logs/app_logs.txt 2>&1 &
```

**Features:**
- ✅ Captures both application logs and Streamlit system messages
- ✅ Runs in background, freeing up terminal
- ✅ All stdout and stderr redirected to file
- ✅ Organized in `logs/` directory (git-ignored)
- ✅ Ideal for extended testing sessions

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

### Method 2: Real-time Log Viewing

Show logs in terminal AND save to file simultaneously:

```bash
mkdir -p logs
uv run streamlit run ui/app.py 2>&1 | tee logs/app_logs_with_console.txt
```

**Features:**
- ✅ Real-time log viewing in terminal
- ✅ Logs also saved to file
- ✅ Interactive - can stop with Ctrl+C
- ✅ Good for active debugging sessions

### Method 3: Different Log Levels

Capture logs with specific verbosity levels:

```bash
# Ensure logs directory exists
mkdir -p logs

# Debug level (most verbose)
APP_ENV=dev LOG_LEVEL=DEBUG uv run streamlit run ui/app.py > logs/debug_logs.txt 2>&1 &

# Info level (default)
LOG_LEVEL=INFO uv run streamlit run ui/app.py > logs/info_logs.txt 2>&1 &

# Warning and error only
LOG_LEVEL=WARNING uv run streamlit run ui/app.py > logs/warning_logs.txt 2>&1 &

# Error only
LOG_LEVEL=ERROR uv run streamlit run ui/app.py > logs/error_only_logs.txt 2>&1 &
```

## Log Analysis

### Understanding Log Format

The application uses structured logging with the following format:
```
TIMESTAMP COMPONENT [LEVEL] MESSAGE
```

Example:
```
2025-08-21 16:28:21 src.agent.tools.interview.pii_redaction [INFO] PII redaction pipeline initialized
```

### Key Components to Monitor

| Component | Description | Common Issues |
|-----------|-------------|---------------|
| `job_search_assistant` | Main application | Configuration errors, startup issues |
| `src.config.manager` | Configuration loading | Missing environment variables, invalid TOML |
| `src.llm.clients` | LLM client connections | API key issues, rate limiting |
| `src.agent.workflows` | Agent execution | Workflow failures, data validation |
| `streamlit` | UI framework | Port conflicts, browser issues |

### Useful Log Analysis Commands

```bash
# Count log levels
grep -c "INFO\|WARNING\|ERROR\|DEBUG" logs/app_logs.txt

# Show only application logs (filter out Streamlit noise)
grep "job_search_assistant\|src\." logs/app_logs.txt

# View logs from specific time range
grep "2025-08-21 16:2[0-9]:" logs/app_logs.txt

# Extract error traces
grep -A 5 -B 2 "ERROR\|Exception\|Traceback" logs/app_logs.txt

# Monitor specific workflow
grep "interview_prep\|job_evaluation" logs/app_logs.txt

# Check API calls
grep -i "api\|request\|response" logs/app_logs.txt
```

## Process Management

### Check Running Processes

```bash
# Find all Streamlit processes
ps aux | grep streamlit

# Check specific process details
ps -p <process_id> -f
```

### Stop the Application

```bash
# Stop by process name
pkill -f "streamlit run ui/app.py"

# Stop by process ID
kill <process_id>

# Force stop if needed
pkill -9 -f "streamlit run ui/app.py"
```

### Stop Log Monitoring

```bash
# Stop log tailing processes
pkill -f "tail -f logs/app_logs.txt"
```

## Common Issues and Solutions

### Issue: No Logs Being Generated

**Problem:** Log file exists but remains empty
**Solution:**
```bash
# Check if app started successfully
ps aux | grep streamlit

# Check for permission issues
ls -la logs/app_logs.txt

# Try manual logging test
mkdir -p logs
echo "Test log entry" >> logs/app_logs.txt
```

### Issue: Logs Show Warning About Missing Questions

**Example Log:**
```
src.agent.workflows.interview_prep.main [WARNING] Generated 0 questions but requested 8
```

**Causes:**
- API key issues preventing LLM calls
- Network connectivity problems
- Rate limiting by LLM provider
- Invalid job description input

**Debug Steps:**
```bash
# Check API connectivity
grep -i "api\|anthropic\|error" logs/app_logs.txt

# Verify environment variables
env | grep -i "anthropic\|api"

# Test with simpler input
# Use shorter job descriptions
```

### Issue: PII Detection Warnings

**Example Log:**
```
presidio-analyzer [WARNING] model_to_presidio_entity_mapping is missing from configuration
```

**Solution:** These warnings are usually harmless. PII detection will fall back to default configurations. To suppress:

```bash
# Run with higher log level to reduce noise
LOG_LEVEL=ERROR uv run streamlit run ui/app.py > app_logs.txt 2>&1 &
```

### Issue: Port Already in Use

**Example Log:**
```
streamlit.cli [ERROR] Port 8501 is already in use
```

**Solution:**
```bash
# Find process using the port
lsof -i :8501

# Kill the process
kill <process_id>

# Or use a different port
uv run streamlit run ui/app.py --server.port 8502
```

## Advanced Debugging

### Enable Debug Mode

```bash
# Maximum verbosity
mkdir -p logs
DEBUG=true LOG_LEVEL=DEBUG uv run streamlit run ui/app.py > logs/debug_full.txt 2>&1 &
```

### Component-Specific Debugging

```bash
# Focus on specific components
grep "interview_prep" logs/app_logs.txt > logs/interview_debug.txt
grep "job_evaluation" logs/app_logs.txt > logs/job_eval_debug.txt
grep "llm" logs/app_logs.txt > logs/llm_debug.txt
```

### Performance Monitoring

```bash
# Monitor timestamp gaps (slow operations)
grep -o "^[0-9-]* [0-9:]*" logs/app_logs.txt | uniq -c

# Track workflow completion times
grep "workflow.*completed\|workflow.*started" logs/app_logs.txt
```

## Log Rotation and Cleanup

### Prevent Large Log Files

```bash
# Limit log file size (rotate when > 10MB)
mkdir -p logs
uv run streamlit run ui/app.py 2>&1 | split -b 10m - logs/app_logs_part_ &

# Archive old logs
tar -czf logs_archive_$(date +%Y%m%d).tar.gz logs/*.txt
```

### Cleanup Commands

```bash
# Remove old log files
rm -f logs/*.txt

# Clean specific patterns
rm -f logs/debug_*.txt logs/error_*.txt
```

## Integration with External Tools

### Send Logs to External Services

```bash
# Send to remote syslog
uv run streamlit run ui/app.py 2>&1 | logger -t job_search_assistant

# Forward to monitoring service
mkdir -p logs
uv run streamlit run ui/app.py 2>&1 | tee logs/app_logs.txt | your_monitoring_tool
```

### Log Analysis Tools

Recommended tools for log analysis:
- **grep/awk/sed**: Built-in Unix tools for pattern matching
- **jq**: If you modify logging to JSON format
- **Elasticsearch/Kibana**: For production log aggregation
- **Grafana**: For log visualization and alerting

## Troubleshooting Checklist

When encountering issues, work through this checklist:

1. **✅ Check process status**
   ```bash
   ps aux | grep streamlit
   ```

2. **✅ Verify log file exists and is being written**
   ```bash
   ls -la logs/app_logs.txt
   tail -5 logs/app_logs.txt
   ```

3. **✅ Check for recent errors**
   ```bash
   grep -i error logs/app_logs.txt | tail -10
   ```

4. **✅ Verify environment setup**
   ```bash
   env | grep -E "(ANTHROPIC|APP_ENV|LANGFUSE)"
   ```

5. **✅ Test basic connectivity**
   ```bash
   curl -s http://localhost:8501 | head -10
   ```

6. **✅ Check system resources**
   ```bash
   df -h     # Disk space
   free -h   # Memory usage
   ```

## Getting Help

If you're still experiencing issues after following this guide:

1. **Gather information:**
   - Full error logs with timestamps
   - System information (`uname -a`)
   - Python version (`python --version`)
   - Environment variables (without sensitive values)

2. **Create a minimal reproduction:**
   - Simplest steps to reproduce the issue
   - Specific input that causes the problem

3. **Check existing resources:**
   - [Installation Guide](installation.md)
   - [Local Development Guide](LOCAL_DEVELOPMENT.md)
   - [Architecture Documentation](architecture.md)

---

**Happy debugging!** 🐛🔍
