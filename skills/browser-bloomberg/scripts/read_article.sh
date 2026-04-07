#!/bin/bash
# Read and summarize Bloomberg article using Chrome CDP
# Usage: bash read_article.sh "BLOOMBERG_URL"

set -e

URL="$1"
if [ -z "$URL" ]; then
    echo "用法: bash read_article.sh \"BLOOMBERG_URL\""
    exit 1
fi

echo "🌐 正在打開: $URL"

# Navigate to URL
agent-browser open "$URL" 2>/dev/null

# Wait for page to load
sleep 5

# Get page content
echo "📖 正在擷取文章內容..."
agent-browser scroll to top 2>/dev/null
sleep 2

# Take snapshot and extract key info
SNAPSHOT=$(agent-browser snapshot -i 2>/dev/null)

# Extract title
TITLE=$(echo "$SNAPSHOT" | grep -oP 'heading "[^"]+' | head -1 | sed 's/heading "//' | sed 's/"//')

# Extract authors
AUTHORS=$(echo "$SNAPSHOT" | grep -oP 'link "[^"]+' | grep -v "Bloomberg\|Subscribe\|Share" | head -5 | tr '\n' ',' | sed 's/,/, /g')

# Extract date
DATE=$(echo "$SNAPSHOT" | grep -oP '\d{4}, \w+ \d{1,2}, \d{4}.*\d{1,2}:\d{2} [A-Z]+' | head -1)

# Extract article body (paragraphs)
BODY=$(echo "$SNAPSHOT" | grep -oP '(?<=StaticText ")[^"]+' | grep -v "^$" | grep -v "Subscribe\|Share\|Advertisement\|Takeaway\|By \|Updated\|Bloomberg" | head -50 | tr '\n' ' ')

# Output results
echo ""
echo "=========================================="
echo "📰 $TITLE"
echo "=========================================="
echo "👤 作者: $AUTHORS"
echo "📅 日期: $DATE"
echo ""
echo "📝 內容:"
echo "$BODY"
echo ""
echo "=========================================="
echo "✅ 文章擷取完成"
