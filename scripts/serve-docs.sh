#!/bin/bash

# Jekyll Documentation Server
# Start the local development server for testing documentation changes

cd "$(dirname "$0")/../docs" || exit 1

echo "🚀 Starting Jekyll documentation server..."
echo "📖 Your documentation will be available at: http://localhost:4000/job_search_assistant/"
echo "Press Ctrl+C to stop the server"
echo ""

bundle exec jekyll serve --incremental --livereload --force_polling
