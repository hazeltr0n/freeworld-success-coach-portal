#!/bin/bash
# Supabase Migration Helper Script
# Quick reference for common migration tasks

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Supabase Migration Helper ===${NC}\n"

# Get Supabase project reference from secrets
PROJECT_REF=$(grep "SUPABASE_URL" .streamlit/secrets.toml | sed 's/.*https:\/\///' | sed 's/\.supabase\.co.*//')

if [ -z "$PROJECT_REF" ]; then
    echo -e "${YELLOW}⚠️  Could not find project reference in .streamlit/secrets.toml${NC}"
    echo "Please ensure SUPABASE_URL is set correctly"
    exit 1
fi

echo -e "${GREEN}✓ Found project: $PROJECT_REF${NC}\n"

# Parse command line arguments
COMMAND=${1:-help}

case "$COMMAND" in
    new)
        # Create a new migration file
        NAME=${2:-migration}
        echo -e "${BLUE}Creating new migration: $NAME${NC}"
        supabase migration new "$NAME"
        echo -e "${GREEN}✓ Migration file created${NC}"
        echo -e "Edit the file in: supabase/migrations/"
        ;;

    push)
        # Push migrations to remote database
        echo -e "${BLUE}Pushing migrations to remote database...${NC}"
        supabase link --project-ref "$PROJECT_REF" 2>/dev/null || true
        supabase db push
        echo -e "${GREEN}✓ Migrations pushed successfully${NC}"
        ;;

    pull)
        # Pull latest schema from remote database
        echo -e "${BLUE}Pulling schema from remote database...${NC}"
        supabase link --project-ref "$PROJECT_REF" 2>/dev/null || true
        supabase db pull
        echo -e "${GREEN}✓ Schema pulled successfully${NC}"
        ;;

    diff)
        # Show diff between local and remote
        echo -e "${BLUE}Checking for schema differences...${NC}"
        supabase link --project-ref "$PROJECT_REF" 2>/dev/null || true
        supabase db diff
        ;;

    reset)
        # Reset local database (WARNING: destructive)
        echo -e "${YELLOW}⚠️  WARNING: This will reset your LOCAL database${NC}"
        read -p "Are you sure? (yes/no): " CONFIRM
        if [ "$CONFIRM" = "yes" ]; then
            supabase db reset
            echo -e "${GREEN}✓ Local database reset${NC}"
        else
            echo "Cancelled"
        fi
        ;;

    link)
        # Link to Supabase project
        echo -e "${BLUE}Linking to project $PROJECT_REF...${NC}"
        supabase link --project-ref "$PROJECT_REF"
        echo -e "${GREEN}✓ Project linked${NC}"
        ;;

    status)
        # Show migration status
        echo -e "${BLUE}Migration status:${NC}"
        supabase migration list
        ;;

    help|*)
        # Show help
        echo "Usage: ./scripts/migrate.sh <command>"
        echo ""
        echo "Commands:"
        echo "  new <name>    Create a new migration file"
        echo "  push          Push migrations to remote database"
        echo "  pull          Pull latest schema from remote database"
        echo "  diff          Show differences between local and remote"
        echo "  status        Show migration status"
        echo "  link          Link to Supabase project"
        echo "  reset         Reset local database (WARNING: destructive)"
        echo ""
        echo "Examples:"
        echo "  ./scripts/migrate.sh new add_new_column"
        echo "  ./scripts/migrate.sh push"
        echo "  ./scripts/migrate.sh diff"
        ;;
esac
