## Features

- Fetch PRs you've authored and reviewed from GitHub repositories
- Analyze the impact of each PR using OpenAI's GPT models
- Generate individual impact statements for each PR
- Create a consolidated brag document summarizing all your contributions
- Generate a self-reflection document mapping your contributions to performance review criteria

## Prerequisites

- Python 3.7 or higher
- GitHub Personal Access Token (with repo scope)
- OpenAI API key or compatible API endpoint

## Installation

Choose one of the following setup methods:

### Option 1: Automated Setup (macOS/Linux)

```bash
git clone https://github.com/moehared/analyze_pr_impact.git
cd analyze_pr_impact
cd "pr analyses"
chmod +x setup.sh
./setup.sh
```

The script will:
- Set Python version to 3.9.15 (using pyenv)
- Create and activate a virtual environment
- Install all required dependencies
- Provide instructions for next steps

### Option 2: Manual Setup

If the script doesn't work, you can manually run these commands

1. Clone this repository:
```bash
git clone https://github.com/moehared/analyze_pr_impact.git
cd analyze_pr_impact
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```


After setup, create your `.env` file as described in the Configuration section below.

## Configuration

Create a `.env` file in the `pr analyses` directory with the following variables:

```
# GitHub Configuration
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_AUTHOR=your_github_username
# For a single repository
GITHUB_REPO_NAME=owner/repo-name
# OR for multiple repositories (comma-separated)
GITHUB_REPO_NAMES=owner/repo1,owner/repo2

# OpenAI API Configuration
OPENAI_API_BASE= 
OPENAI_API_KEY=your_openai_api_key
```

### GitHub Token

Generate a GitHub Personal Access Token with `repo` scope at [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens).

### Repository Configuration

You can specify repositories in two ways:
- `GITHUB_REPO_NAME`: For a single repository (e.g., `Shopify/repo-name`)
- `GITHUB_REPO_NAMES`: For multiple repositories as a comma-separated list (e.g., `Shopify/repo-name, Shopify/repo-name-2`)

If both are specified, `GITHUB_REPO_NAMES` takes precedence.

## Usage

After completing any of the setup options above, run the analysis script:

```bash
# If you're not already in the "pr analyses" directory
cd "pr analyses"

# Run the script
python pr_analyses.py
```

The script will:
1. Fetch your PRs (both authored and reviewed) from the specified repositories
2. Analyze each PR's impact using OpenAI
3. Generate individual markdown files for each PR analysis
4. Create a consolidated brag document summary
5. Generate a self-reflection document mapping your contributions to performance criteria

Output files will be placed in a directory named `PR_Analysis_[repo-name]_[username]_[date]`.

## Customizing Date Range

By default, the tool analyzes PRs from September 2024 to March 2025. To modify this date range, open `pr_analyses.py` and update these lines:

```python
# Define specific date range
start_date = datetime.datetime(2024, 9, 1)  # September 1, 2024
end_date = datetime.datetime(2025, 4, 1)   # April 1, 2025
```

## Example Output

The tool generates three types of files:

1. **Individual PR Analysis Files**: Detailed impact analysis for each PR
2. **Brag Document Summary**: Consolidated summary of all your contributions
3. **Self-Reflection Document**: Maps your contributions to performance criteria


### No PRs Found

If no PRs are found, check:
- Your GitHub username is correct in `.env`
- The repositories exist and you have access to them
- Your date range covers periods when you were active
- Your GitHub token has sufficient permissions
