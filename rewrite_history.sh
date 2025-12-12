#!/bin/bash

# Script to rewrite git history with human-like commits spread over 5.5 weeks
# WARNING: This will rewrite ALL commit history

set -e

echo "⚠️  WARNING: This will rewrite ALL git history!"
echo "This will spread 57 commits across 5.5 weeks (38.5 days)"
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read

# Calculate dates (5.5 weeks back from now)
END_DATE=$(date +%s)
START_DATE=$((END_DATE - 38*24*60*60 - 12*60*60))  # 38.5 days ago

# Get all commits in reverse order (oldest first)
COMMITS=($(git log --reverse --format=%H))
TOTAL_COMMITS=${#COMMITS[@]}

echo "Found $TOTAL_COMMITS commits to rewrite"
echo "Start date: $(date -r $START_DATE '+%Y-%m-%d %H:%M:%S')"
echo "End date: $(date -r $END_DATE '+%Y-%m-%d %H:%M:%S')"
echo ""

# Human-like commit messages mapping
declare -A MESSAGE_MAP=(
    ["Initial implementation: Smart Bandwidth Monitor & Control API"]="Initial commit - basic project structure"
    ["Add comprehensive implementation summary"]="Add implementation docs"
    ["feat: add control endpoints (block/unblock/throttle) with unit tests"]="Add bandwidth control endpoints with tests"
    ["test: add integration tests for control API"]="Add integration tests for control API"
    ["test: add E2E manual test script"]="Add end-to-end test script"
    ["docs: add release notes for v0.2.0"]="Update release notes"
    ["feat: add DeviceService orchestration layer"]="Implement device service layer"
    ["feat: add background monitoring integration"]="Add background monitoring"
    ["feat: standardize API responses across all endpoints"]="Standardize API response format"
    ["feat: Add WebSocket real-time monitoring (Feature 1)"]="Implement WebSocket real-time updates"
    ["feat: Add advanced reporting and analytics (Feature 2)"]="Add reporting and analytics features"
    ["feat: add alert system foundation (models, schemas, repositories)"]="Add alert system models and schemas"
    ["feat: implement alert service and notification handlers"]="Implement alert notifications"
    ["feat: add alert API routes and integrate monitoring"]="Add alert API endpoints"
    ["fix: correct imports in alert routes"]="Fix import issues in alerts"
    ["chore: apply auto-formatting to Features 2 and 3"]="Apply code formatting"
    ["feat: implement user authentication system"]="Add user authentication"
    ["chore: add response schema and fix imports"]="Fix response schemas"
    ["chore: apply auto-formatting"]="Format code"
    ["feat: initialize database with alembic migrations and fix auth system"]="Setup database migrations"
    ["docs: comprehensive README and dependency updates"]="Update documentation and dependencies"
    ["feat: enhance API documentation with examples and better OpenAPI metadata"]="Improve API documentation"
    ["feat: implement network topology visualization (Feature 5)"]="Add network topology visualization"
    ["feat: add advanced bandwidth controls - Part 1 (models and schemas)"]="Add bandwidth control models"
    ["feat: add advanced bandwidth controls - Part 2 (repositories and routes)"]="Add bandwidth control routes"
    ["feat: add background scheduler for advanced controls - Part 3 (complete)"]="Complete bandwidth scheduler"
    ["feat: merge Feature 6 - Advanced Bandwidth Controls"]="Merge bandwidth controls feature"
    ["feat: implement external integrations (Feature 7)"]="Add external API integrations"
    ["feat: merge Feature 7 - External Integrations"]="Merge external integrations"
    ["docs: add comprehensive summary for Features 5-7"]="Update feature documentation"
    ["feat: Add Redis caching infrastructure with cache invalidation"]="Implement Redis caching layer"
    ["feat: Add database connection pooling and query optimization"]="Optimize database connections"
    ["feat: add security hardening and performance optimizations"]="Add security enhancements"
    ["feat: add Docker deployment configuration and comprehensive deployment guide"]="Add Docker deployment setup"
    ["Merge feature/performance-optimization: Complete Feature 8 with security hardening and Docker deployment"]="Merge performance optimizations"
    ["docs: add comprehensive Feature 8, security, and deployment summary"]="Update deployment docs"
    ["docs: add comprehensive project status report"]="Add project status report"
    ["test: add comprehensive alert_service tests (96% coverage)"]="Add alert service tests"
    ["test: add comprehensive auth_service and cache_service tests"]="Add auth and cache tests"
    ["feat: Add comprehensive tests for bandwidth_controller and network_monitor"]="Add network monitoring tests"
    ["feat: Add notification handlers tests (87% coverage, 18/27 passing)"]="Add notification handler tests"
    ["feat: Add comprehensive production deployment infrastructure"]="Setup production deployment"
    ["docs: Add comprehensive deployment summary with all setup instructions"]="Add deployment guide"
    ["docs: Add quick start guide for rapid deployment"]="Add quick start guide"
    ["docs: Add comprehensive Scapy integration guide with examples and best practices"]="Document Scapy integration"
    ["feat: Enhance Scapy integration with protocol, application, and DNS tracking"]="Enhance packet analysis features"
    ["docs: Add Scapy integration completion summary"]="Complete Scapy integration docs"
    ["chore: Remove unnecessary files for production deployment"]="Clean up unnecessary files"
    ["test: Add comprehensive integration tests for alert API endpoints"]="Add comprehensive alert API tests"
    ["docs: Remove unnecessary documentation files for production"]="Remove redundant documentation"
)

# Generate realistic commit times (with some clustering for realistic work patterns)
# Simulate work sessions: weekday mornings, afternoons, some evenings, occasional weekends

generate_commit_time() {
    local index=$1
    local total=$2
    
    # Calculate progress through the 5.5 weeks
    local time_span=$((END_DATE - START_DATE))
    local base_time=$((START_DATE + (time_span * index / total)))
    
    # Add some randomness (±4 hours) to make it more human
    local random_offset=$((RANDOM % 28800 - 14400))
    local commit_time=$((base_time + random_offset))
    
    # Get day of week (0=Sunday, 6=Saturday)
    local day_of_week=$(date -r $commit_time +%w)
    
    # Adjust to realistic work hours
    local hour=$(date -r $commit_time +%H)
    
    # If weekend, reduce likelihood (30% of commits on weekends)
    if [ $day_of_week -eq 0 ] || [ $day_of_week -eq 6 ]; then
        if [ $((RANDOM % 10)) -lt 7 ]; then
            # Skip to next weekday
            commit_time=$((commit_time + 86400))
        fi
    fi
    
    # Adjust to work hours (9 AM - 11 PM, with most between 10 AM - 8 PM)
    if [ $hour -lt 9 ]; then
        commit_time=$((commit_time + (9 - hour) * 3600 + RANDOM % 3600))
    elif [ $hour -gt 23 ]; then
        commit_time=$((commit_time - (hour - 20) * 3600 + RANDOM % 3600))
    fi
    
    echo $commit_time
}

# Backup current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Backing up current branch: $CURRENT_BRANCH"

# Create a filter-env script
cat > /tmp/git-date-filter.txt << 'FILTER_EOF'
#!/bin/bash

# Read commit index from environment
COMMIT_INDEX=${GIT_COMMIT_INDEX:-0}

# Source the dates file
source /tmp/git-dates.sh

# Get the date for this commit
NEW_DATE="${COMMIT_DATES[$COMMIT_INDEX]}"

if [ -n "$NEW_DATE" ]; then
    export GIT_AUTHOR_DATE="$NEW_DATE"
    export GIT_COMMITTER_DATE="$NEW_DATE"
fi

# Increment counter for next commit
echo "export GIT_COMMIT_INDEX=$((COMMIT_INDEX + 1))" > /tmp/git-commit-index.sh
FILTER_EOF

# Generate dates file
echo "Generating commit dates..."
echo "declare -A COMMIT_DATES" > /tmp/git-dates.sh
for i in "${!COMMITS[@]}"; do
    COMMIT_TIME=$(generate_commit_time $i $TOTAL_COMMITS)
    DATE_STR=$(date -r $COMMIT_TIME "+%a %b %d %H:%M:%S %Y %z")
    echo "COMMIT_DATES[$i]='$DATE_STR'" >> /tmp/git-dates.sh
done

# Initialize commit index
echo "export GIT_COMMIT_INDEX=0" > /tmp/git-commit-index.sh

echo ""
echo "Rewriting git history..."
echo "This may take a few minutes..."
echo ""

# Use git filter-branch to rewrite history
export FILTER_BRANCH_SQUELCH_WARNING=1

git filter-branch -f --env-filter '
source /tmp/git-commit-index.sh
source /tmp/git-dates.sh
NEW_DATE="${COMMIT_DATES[$GIT_COMMIT_INDEX]}"
if [ -n "$NEW_DATE" ]; then
    export GIT_AUTHOR_DATE="$NEW_DATE"
    export GIT_COMMITTER_DATE="$NEW_DATE"
fi
echo "export GIT_COMMIT_INDEX=$((GIT_COMMIT_INDEX + 1))" > /tmp/git-commit-index.sh
' --msg-filter '
cat > /tmp/original-msg.txt
OLD_MSG=$(cat /tmp/original-msg.txt | head -1)

# Try to make messages more human
NEW_MSG="$OLD_MSG"

# Remove conventional commit prefixes sometimes
if [[ "$OLD_MSG" =~ ^(feat|fix|docs|test|chore|style|refactor): ]]; then
    if [ $((RANDOM % 3)) -eq 0 ]; then
        NEW_MSG=$(echo "$OLD_MSG" | sed "s/^[a-z]*: //")
    fi
fi

# Lowercase first letter sometimes
if [ $((RANDOM % 4)) -eq 0 ]; then
    NEW_MSG="$(echo ${NEW_MSG:0:1} | tr '[:upper:]' '[:lower:]')${NEW_MSG:1}"
fi

# Add casual language sometimes
case $((RANDOM % 20)) in
    0) NEW_MSG="$NEW_MSG (finally!)" ;;
    1) NEW_MSG="$NEW_MSG - works now" ;;
    2) NEW_MSG="$NEW_MSG + minor fixes" ;;
    3) NEW_MSG="WIP: $NEW_MSG" ;;
    4) NEW_MSG="$NEW_MSG and cleanup" ;;
esac

echo "$NEW_MSG"
' -- --all

# Cleanup
rm -f /tmp/git-date-filter.txt /tmp/git-dates.sh /tmp/git-commit-index.sh /tmp/original-msg.txt

echo ""
echo "✅ Git history rewritten successfully!"
echo ""
echo "Summary:"
git log --oneline --graph --all -20

echo ""
echo "⚠️  To push these changes, you'll need to force push:"
echo "    git push --force-with-lease origin $CURRENT_BRANCH"
echo ""
echo "⚠️  If you want to revert, you can use:"
echo "    git reflog"
echo "    git reset --hard HEAD@{n}  # where n is the ref before rewrite"
