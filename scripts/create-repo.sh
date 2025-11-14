#!/bin/bash

# Automated Repository Creation Script for Meta Mega Orchestration Teams
# Usage: ./scripts/create-repo.sh <repo-name> "<description>"

# --- Configuration ---
DEFAULT_BRANCH="main"
# The organization name is inferred from the gh CLI context, but can be set here if needed.
# ORG_NAME="Loofy147"

# --- Functions ---

# Function to check if a command exists
command_exists () {
  command -v "$1" >/dev/null 2>&1
}

# Function to validate the repository name against the standard
validate_name() {
    local name="$1"
    # Regex for <team-or-project>-<technology-stack>-<description>
    if [[ ! "$name" =~ ^[a-z0-9]+(-[a-z0-9]+){2,}$ ]]; then
        echo "Error: Repository name '$name' does not follow the standard naming convention:"
        echo "Format: <team-or-project>-<technology-stack>-<description>"
        echo "Rules: All lowercase, separated by hyphens, at least three components."
        exit 1
    fi
}

# Function to create the standard directory structure
create_standard_structure() {
    echo "Creating standard directory structure..."
    mkdir -p .github/ISSUE_TEMPLATE .github/workflows docs src tests scripts
    touch README.md .gitignore .github/workflows/ci-cd.yml
    
    # Copy issue templates from the core repo
    cp ../.github/ISSUE_TEMPLATE/bug_report.md .github/ISSUE_TEMPLATE/
    cp ../.github/ISSUE_TEMPLATE/feature_request.md .github/ISSUE_TEMPLATE/

    # Copy the standard CI/CD workflow template
    cp ../.github/workflows/ci-cd.yml .github/workflows/
}

# --- Main Execution ---

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <repo-name> \"<description>\""
    echo "Example: $0 alpha-team-python-data-service \"Data ingestion and processing service for Alpha Team\""
    exit 1
fi

REPO_NAME="$1"
DESCRIPTION="$2"

# 1. Check for gh CLI
if ! command_exists gh; then
    echo "Error: GitHub CLI (gh) is not installed or not in PATH."
    exit 1
fi

# 2. Validate Naming Convention
validate_name "$REPO_NAME"

# 3. Create the repository
echo "Creating GitHub repository: $REPO_NAME"
gh repo create "$REPO_NAME" --public --description "$DESCRIPTION" --add-readme --default-branch "$DEFAULT_BRANCH"

if [ $? -ne 0 ]; then
    echo "Error: Failed to create repository $REPO_NAME. It may already exist or you lack permissions."
    exit 1
fi

# 4. Clone the new repository
echo "Cloning $REPO_NAME..."
gh repo clone "$REPO_NAME"

if [ $? -ne 0 ]; then
    echo "Error: Failed to clone repository $REPO_NAME."
    exit 1
fi

# 5. Initialize standard structure
cd "$REPO_NAME" || exit 1
create_standard_structure

# 6. Commit and Push
echo "Committing initial structure..."
git add .
git commit -m "feat: Initial commit with enterprise standard structure"
git push origin "$DEFAULT_BRANCH"

# 7. Finalize
echo "Repository $REPO_NAME created and initialized successfully!"
echo "Local directory: $(pwd)"
echo "Remote URL: https://github.com/$(gh api user --jq '.login')/$REPO_NAME"

# --- Post-Creation Note (Branch Protection) ---
echo ""
echo "--- IMPORTANT: MANUAL STEP REQUIRED ---"
echo "Branch protection rules for 'main' and 'develop' must be set manually or via a separate automation tool (e.g., Terraform or dedicated GitHub API calls) as the 'gh' CLI does not support this directly."
echo "Recommended Rules:"
echo " - Require a pull request before merging"
echo " - Require approvals (e.g., 2)"
echo " - Require status checks to pass"
echo " - Require linear history"
echo " - Restrict who can push to matching branches"
