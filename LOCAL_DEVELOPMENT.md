# Local Jekyll Development

This guide explains how to test documentation changes locally before deploying to GitHub Pages.

## Quick Start

1. **Start the development server:**
   ```bash
   ./scripts/serve-docs.sh
   ```

2. **Open your browser to:**
   ```
   http://localhost:4000/job_search_assistant/
   ```

3. **Make changes to any `.md` files and see them automatically reload in your browser!**

## Manual Setup

If you prefer to run commands manually:

### First-time setup (already completed):
```bash
# Install dependencies (only needed once)
cd docs
bundle install
```

### Starting the server:
```bash
# Start Jekyll development server
cd docs
bundle exec jekyll serve --incremental --livereload
```

## Available Commands

| Command | Description |
|---------|-------------|
| `./scripts/serve-docs.sh` | Start development server with auto-reload |
| `bundle exec jekyll serve` | Start basic development server |
| `bundle exec jekyll serve --incremental` | Faster builds for large sites |
| `bundle exec jekyll serve --livereload` | Auto-refresh browser on changes |
| `bundle exec jekyll build` | Build site to `_site/` folder |

## Development Workflow

1. **Edit documentation:** Modify any `.md` file in the `docs/` folder
2. **Preview locally:** Changes appear automatically at `http://localhost:4000/job_search_assistant/`
3. **Test thoroughly:** Navigate through all pages to ensure links work
4. **Commit and push:** Your changes will be deployed to GitHub Pages automatically

## File Structure

```
docs/
├── _config.yml           # Jekyll configuration
├── Gemfile              # Ruby dependencies
├── serve.sh             # Convenience script
├── index.md             # Homepage
├── README.md            # Documentation index
├── architecture.md      # Architecture overview
├── installation.md      # Installation guide
└── design/              # Design documentation
    ├── README.md
    ├── configuration.md
    ├── job-evaluation-design.md
    └── agent-infrastructure.md
```

## GitHub Pages Compatibility

This setup uses the `github-pages` gem, which ensures your local environment exactly matches GitHub Pages. This means:
- ✅ Same Jekyll version as GitHub Pages
- ✅ Same plugins and themes
- ✅ Same markdown processor and settings
- ✅ What you see locally is what gets deployed

## Troubleshooting

### Server won't start
```bash
# Update dependencies
bundle update

# Clear Jekyll cache
bundle exec jekyll clean
```

### Port already in use
```bash
# Use a different port
bundle exec jekyll serve --port 4001
```

### Changes not appearing
- Make sure you saved the file
- Check the terminal for build errors
- Try refreshing the browser (Ctrl/Cmd + R)

---

**Happy documenting!** 📚✨
