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
- `GITHUB_REPO_NAME`: For a single repository (e.g., `owner/repo-name`)
- `GITHUB_REPO_NAMES`: For multiple repositories as a comma-separated list (e.g., `owner/repo1,owner/repo2`)

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

## Customizing the Prompt

You can fully customize the prompt used for PR analysis by editing the `prompt.txt` file in the project root. This file controls the instructions and format given to the AI for generating impact statements.

- The script will use the contents of `prompt.txt` as the prompt template.
- You can use placeholders like `{pr_title}`, `{pr_url}`, `{pr_description}`, `{pr_changed_files}`, `{pr_additions}`, and `{pr_deletions}` which will be filled in with PR data.
- If you delete or rename `prompt.txt`, the script will use a generic default prompt.

**Example `prompt.txt`:**
```
Analyze this Pull Request and create an impact statement following the format below:

PR Title: {pr_title}
PR URL: {pr_url}
PR Description: {pr_description}
Changed Files: {pr_changed_files}
Additions: {pr_additions}
Deletions: {pr_deletions}

Your response must follow this format:

I shipped this {pr_url} that [quick TLDR of the PR], which did the following:
- [Key bullet point about what the PR accomplished]
- [Another key bullet point]
- [Additional bullet point if needed]

This is impactful because:
- [Specific impact point]
- [Another impact point]
- [Additional impact point if relevant]
```

Feel free to edit `prompt.txt` to match your preferred style or requirements!

## Customizing the Self-Reflection Prompt

You can fully customize the prompt used for generating the self-reflection document by editing the `self_reflection_prompt.txt` file in the project root. This file controls the instructions and format given to the AI for mapping your PR contributions to your organization's performance review criteria.

- The script will use the contents of `self_reflection_prompt.txt` as the prompt template.
- You can use placeholders like `{brag_doc_content}` and `{performance_criteria}` which will be filled in with your brag document and your organization's criteria.
- If you delete or rename `self_reflection_prompt.txt`, the script will use a generic default prompt.

**Example `self_reflection_prompt.txt`:**
```
You are provided with a brag document that summarizes my contributions through PRs I've authored and reviewed. Please create a compelling self-reflection document that maps these contributions to my organization's performance review criteria.

Here is the brag document content (please reference specific PRs in your analysis):
{brag_doc_content}

Here are the performance review criteria for my role:
{performance_criteria}

For your self-reflection document, please:
1. Start with a specific introduction about my impact during this period.
2. Create separate sections for each major project or area of work.
   - For each section, highlight the most significant PRs from the brag doc that demonstrate exceptional impact.
   - Map each PR to a specific performance criterion.
   - For each PR, explain:
       * What technical or business challenge I solved
       * How I approached the solution
       * Why this demonstrates the specific skill or responsibility
       * The quantifiable or qualitative impact this work had
   - Use direct quotes from the brag doc where appropriate
3. Include a section on mentorship, collaboration, or leadership if relevant.
4. Include a section highlighting how I exceeded expectations or went beyond basic requirements.
5. End with a forward-looking conclusion summarizing my growth and future goals.

IMPORTANT:
- Be specific, not generic—reference precise PRs and their outcomes
- Use concrete examples from the brag doc
- Show how each contribution demonstrates a specific performance criterion
- Make this compelling and impressive
- Include PR links (using markdown format) when referencing specific PRs
- Structure should be clear with headers for each section and subsection
- Format the document in markdown with clear headers, bullet points, and links to PRs where appropriate.
```

Feel free to edit `self_reflection_prompt.txt` to match your preferred style or requirements!

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
