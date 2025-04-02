import os
import datetime
from dateutil.relativedelta import relativedelta
import requests
from github import Github
from github.GithubException import GithubException
from openai import OpenAI
# Make pandas import optional since we're not using it heavily
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
from dotenv import load_dotenv
import json
import time

# Load environment variables
load_dotenv()

# Initialize API clients
def initialize_github_client():
    """Initialize and return a GitHub client."""
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        raise ValueError("GITHUB_TOKEN not found in environment variables")
    return Github(github_token)

def initialize_openai_client():
    """Initialize and return an OpenAI client."""
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_api_base = os.getenv("OPENAI_API_BASE")
    
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    if not openai_api_base:
        raise ValueError("OPENAI_API_BASE not found in environment variables")
    
    # Clean, simple initialization
    return OpenAI(
        api_key=openai_api_key,
        base_url=openai_api_base
    )

# PR Fetching
def fetch_prs(github_client, repo_name, start_date=None, end_date=None, author=None, merged_only=False):
    """
    Fetch PRs from the specified repository within a date range.
    Optionally filter by author username and merged status.
    """
    # Default to last 6 months if no dates specified
    if not end_date:
        end_date = datetime.datetime.now()
    if not start_date:
        start_date = end_date - relativedelta(months=6)
        
    print(f"Fetching PRs from {repo_name} between {start_date.strftime('%Y-%m-%d')} and {end_date.strftime('%Y-%m-%d')}...")
    if author:
        print(f"Filtering for PRs authored by: {author}")
    if merged_only:
        print("Filtering for merged PRs only")
    
    try:
        user = github_client.get_user()
        print(f"Authenticated as: {user.login}")
        
        repo = github_client.get_repo(repo_name)
        print(f"Successfully accessed repository: {repo.full_name}")
        
        # Get all closed PRs
        prs = repo.get_pulls(state='closed', sort='updated', direction='desc')
        
        relevant_prs = []
        for pr in prs:
            # Skip if we're filtering by author and this PR isn't by that author
            if author and pr.user.login != author:
                continue
                
            # Skip if we only want merged PRs and this one wasn't merged
            if merged_only and not pr.merged:
                continue
                
            # Check if the PR was merged within our date range
            merge_date = pr.merged_at if pr.merged else None
            
            if merge_date and merge_date >= start_date and merge_date <= end_date:
                relevant_prs.append({
                    'number': pr.number,
                    'title': pr.title,
                    'description': pr.body,
                    'url': pr.html_url,
                    'created_at': pr.created_at.strftime('%Y-%m-%d'),
                    'merged_at': merge_date.strftime('%Y-%m-%d') if merge_date else None,
                    'author': pr.user.login,
                    'changed_files': pr.changed_files,
                    'additions': pr.additions,
                    'deletions': pr.deletions,
                })
            # Stop if we've gone beyond our time range
            elif merge_date and merge_date < start_date:
                break
                
        if author:
            print(f"Found {len(relevant_prs)} {'merged ' if merged_only else ''}PRs by {author} in the specified time range.")
        else:
            print(f"Found {len(relevant_prs)} {'merged ' if merged_only else ''}PRs in the specified time range.")
        return relevant_prs
    except GithubException as e:
        if e.status == 404:
            print(f"Error: Repository '{repo_name}' not found or not accessible with current token.")
            print("If this is a private repository, please check your token permissions.")
            print(f"Detailed error: {e}")
        else:
            print(f"GitHub API error: {e}")
        return []
    except Exception as e:
        print(f"Error fetching PRs: {e}")
        return []

# PR Fetching modifications to include PRs you reviewed
def fetch_prs_reviewed(github_client, repo_name, start_date=None, end_date=None, reviewer=None):
    """Fetch PRs that were reviewed by the specified user, excluding PRs they authored."""
    if not end_date:
        end_date = datetime.datetime.now()
    if not start_date:
        start_date = end_date - relativedelta(months=6)
        
    print(f"Fetching PRs reviewed by {reviewer} between {start_date.strftime('%Y-%m-%d')} and {end_date.strftime('%Y-%m-%d')}...")
    print(f"Excluding PRs authored by {reviewer}")
    
    try:
        repo = github_client.get_repo(repo_name)
        # Get all merged PRs
        prs = repo.get_pulls(state='closed', sort='updated', direction='desc')
        
        reviewed_prs = []
        for pr in prs:
            # Skip if PR wasn't merged or is outside our date range
            if not pr.merged or pr.merged_at < start_date or pr.merged_at > end_date:
                continue
                
            # Skip if the reviewer is also the author (exclude self-authored PRs)
            if pr.user.login == reviewer:
                continue
            
            # Skip if PR title contains "translation" or "translations"
            if "translation" in pr.title.lower():
                print(f"Skipping translation PR #{pr.number}: {pr.title}")
                continue
                
            # Check if user reviewed this PR
            reviews = list(pr.get_reviews())
            user_reviews = [review for review in reviews if review.user.login == reviewer]
            
            # Skip if user has fewer than 2 substantive review comments
            substantive_reviews = []
            for review in user_reviews:
                if review.body and len(review.body.strip()) > 10:  # Consider a comment substantive if > 10 chars
                    substantive_reviews.append(review.body)
                    
            if len(substantive_reviews) < 2:
                print(f"Skipping PR #{pr.number} with fewer than 2 substantive comments")
                continue
            
            if user_reviews:
                # User reviewed this PR
                review_comments = []
                for review in user_reviews:
                    if review.body and review.body.strip():
                        review_comments.append(review.body)
                
                reviewed_prs.append({
                    'number': pr.number,
                    'title': pr.title,
                    'description': pr.body,
                    'url': pr.html_url,
                    'author': pr.user.login,
                    'created_at': pr.created_at.strftime('%Y-%m-%d'),
                    'merged_at': pr.merged_at.strftime('%Y-%m-%d'),
                    'user_reviews': review_comments,
                    'changed_files': pr.changed_files,
                    'additions': pr.additions,
                    'deletions': pr.deletions,
                })
        
        print(f"Found {len(reviewed_prs)} PRs reviewed by {reviewer} (excluding self-authored PRs) in the specified time range.")
        return reviewed_prs
    except Exception as e:
        print(f"Error fetching reviewed PRs: {e}")
        return []

# PR Analysis with OpenAI
def analyze_pr_impact(openai_client, pr_data, is_authored=True):
    """Analyze the impact of a PR using OpenAI."""
    print(f"Analyzing {'authored' if is_authored else 'reviewed'} PR #{pr_data['number']}: {pr_data['title']}")
    
    # Construct different prompts based on whether the PR was authored or reviewed
    if is_authored:
        prompt = f"""
        Analyze this Pull Request that I authored and create an impact statement following the exact format shown below:
        
        PR Title: {pr_data['title']}
        PR URL: {pr_data['url']}
        PR Description: {pr_data['description'] or 'No description provided'}
        Changed Files: {pr_data['changed_files']}
        Additions: {pr_data['additions']}
        Deletions: {pr_data['deletions']}
        
        Your response must follow this exact format:

        I shipped this {pr_data['url']} that [quick TLDR of the PR], which did the following:

        - [Key bullet point about what the PR accomplished]
        - [Another key bullet point]
        - [Additional bullet point if needed]

        This is impactful because:

        - [Specific impact point]
        - [Another impact point]
        - [Additional impact point if relevant]

        Here's an example of the format and depth I'm looking for:

        I shipped this @https://github.com/Shopify/react-native-customerview/pull/2821 that updates our handling of Stripe's error messages for location mismatches, which did the following:

        - Updated Error Parsing Logic: Adjusted our parsing logic to handle the new SDK error message for location mismatches appropriately, ensuring that our UX messages are displayed correctly based on the updated error format.
        - Created Maintenance Issue: Documented the need to address location mismatches when paymentCollect fails as a separate issue in our maintenance cycle.
        - Improved UX Messaging: Initiated the creation of a new issue to improve UX messaging for pre-existing reader location mismatches, similar to the UX displayed for Stripe currency mismatches.

        This is impactful because:

        - Ensured Correct Error Handling: Updating the error parsing logic ensures that our application correctly handles and displays relevant error messages, maintaining a seamless user experience.
        - Proactive Maintenance: Creating a separate maintenance issue ensures that the necessary changes are tracked and addressed in an organized manner, preventing future disruptions.
        - Enhanced User Experience: Improving UX messaging for location mismatches aligns with our goal of providing clear and helpful feedback to users, similar to our handling of currency mismatches.
        """
    else:
        # For reviewed PRs
        review_comments = "\n".join(pr_data.get('user_reviews', []))
        prompt = f"""
        Analyze this Pull Request that I reviewed and create an impactful review statement:
        
        PR Title: {pr_data['title']}
        PR URL: {pr_data['url']}
        PR Author: {pr_data['author']}
        My Review Comments: {review_comments or 'Review comments not available'}
        
        Your response must follow this exact format:

        I provided key review for {pr_data['url']} that [brief description of the PR], where I contributed the following:

        - [Specific contribution from your review]
        - [Another specific contribution]
        - [Additional contribution if relevant]

        This review was impactful because:

        - [Specific impact of your review]
        - [Another impact point]
        - [Additional impact if relevant]
        """
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert at creating impactful brag documents for software engineers. Create specific, concrete, and detailed impact statements that precisely follow the requested format."},
                {"role": "user", "content": prompt}
            ]
        )
        analysis = response.choices[0].message.content
        return analysis
    except Exception as e:
        print(f"Error analyzing PR: {e}")
        return f"Error analyzing PR: {e}"

# New file output functions
def create_output_directory(dir_name="pr_analyses_output"):
    """Create a directory for output files if it doesn't exist."""
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    return dir_name

def write_pr_analysis_to_file(pr_data, analysis, output_dir):
    """Write PR analysis to a markdown file."""
    filename = f"PR_{pr_data['number']}_{pr_data['title'].replace(' ', '_')[:30]}.md"
    # Remove any invalid characters from filename
    filename = ''.join(c for c in filename if c.isalnum() or c in ['_', '-', '.'])
    
    filepath = os.path.join(output_dir, filename)
    
    # Safely get values with defaults for potentially missing fields
    created_at = pr_data.get('created_at', 'Not available')
    merged_at = pr_data.get('merged_at', 'Not merged')
    changed_files = pr_data.get('changed_files', 'N/A')
    additions = pr_data.get('additions', 'N/A')
    deletions = pr_data.get('deletions', 'N/A')
    
    content = f"""# PR #{pr_data['number']} - {pr_data['title']} - Impact Analysis

PR URL: {pr_data['url']}
Author: {pr_data['author']}
Created: {created_at}
Merged: {merged_at}
Changed Files: {changed_files}
Additions: {additions}
Deletions: {deletions}

## Impact Analysis

{analysis}
"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath

def create_brag_doc_summary(authored_analyses, reviewed_analyses, repo_name, output_dir):
    """Create a brag doc summary markdown file."""
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    filename = f"Brag_Doc_Summary_{repo_name.replace('/', '_')}_{today}.md"
    filepath = os.path.join(output_dir, filename)
    
    summary_content = f"""# Impact Assessment Brag Document

Repository: {repo_name}
Assessment Period: September 2024 - March 2025
Analysis Date: {today}

## PRs Authored: Key Contributions & Impact

"""
    
    # Add authored PRs
    for analysis in authored_analyses:
        summary_content += f"- {analysis['analysis']}\n\n"
    
    summary_content += "\n## PRs Reviewed: Key Contributions & Impact\n\n"
    
    # Add reviewed PRs
    for analysis in reviewed_analyses:
        summary_content += f"- {analysis['analysis']}\n\n"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(summary_content)
    
    return filepath

def generate_self_reflection(openai_client, brag_doc_path, output_dir):
    """Generate a self-reflection document that maps PR contributions to Shopify OS requirements."""
    print("Generating self-reflection document based on PR contributions...")
    
    # Read the brag doc summary
    with open(brag_doc_path, 'r', encoding='utf-8') as f:
        brag_doc_content = f.read()
    
    prompt = f"""
    I'm going to provide you with a brag document that summarizes my contributions through PRs I've authored and reviewed. 
    Please create a compelling self-reflection document that maps these contributions to Shopify's OS which is a leveling system requirements for the C5 or mid level role.

    Here's the brag document content (please read this carefully and reference specific PRs in your analysis):
    {brag_doc_content}

    Here are the C5 requirements from Shopify's OS:

    C5 Requirements
    Craft Skills
    - Execute well on defined problems. Learn continuously.
    - Write code that is easy to understand, operate, and maintain.
    - Know all the important details.
    - Do things fast.

    Responsibilities To The Craft/Job
    - Constantly charge your trust battery and make your team better.
    - Leverage data effectively to build great things and make great decisions.
    - Care deeply about the quality and proper usage of the data that powers your work.
    
    Responsibilities To Shopify
    - Treat project requirements as a minimum floor. Be ambitious about raising the ceiling

    For your self-reflection document, STRICTLY follow this format and guidance:

    1. Start with a compelling, specific introduction about my impact during this period, mentioning both the CV Foundation and CV Compat projects specifically.
    
    2. Create separate sections for EACH project:
       - "CV Foundation Project Impact" - Focus on my most significant PRs for this project
       - "CV Compat Project Impact" - Focus on my most significant PRs for this project
       
    3. Within each project section:
       - Select the 3-4 MOST impressive PRs from the brag doc that demonstrate exceptional impact
       - Map each PR to a specific OS requirement (Craft Skills and Responsibilities)
       - For each PR, explain IN DETAIL:
           * What technical challenge I solved
           * How I approached the solution 
           * Why this approach demonstrates the specific OS skill/responsibility
           * The quantifiable impact this work had (user experience, performance, maintenance)
       - Use direct quotes from the brag doc where appropriate
    
    4. Include a "Mentorship and Leadership" section where you discuss how I mentored Sally, an intern:
       - How I helped with her development setup
       - Our pair programming sessions
       - Answering her technical questions
       - How this demonstrates leadership qualities from the OS

    5. Include a "Beyond Requirements" section highlighting how I exceeded minimum expectations and raised the ceiling
       - Find examples from the brag doc of work that went beyond basic requirements
       - Explain how this demonstrates ambition and commitment to excellence
    
    6. End with a forward-looking conclusion that:
       - Summarizes my growth across both projects
       - Highlights my most significant contributions
       - Shows my excitement to continue developing in specific areas
    
    IMPORTANT:
    - Be SPECIFIC, not generic - reference precise PRs and their outcomes
    - Use CONCRETE examples from the brag doc, not vague statements
    - Show HOW each contribution demonstrates a specific OS skill
    - Make this compelling and IMPRESSIVE - it should showcase exceptional impact
    - Include PR links (using markdown format) when referencing specific PRs
    - Structure should be clear with headers for each section and subsection
    - Be substantive - this is a major document that should demonstrate deep impact
    
    Format the document in markdown with clear headers, bullet points, and links to PRs where appropriate.
    """
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert at creating impressive, detailed self-reflection documents for performance reviews. You carefully analyze provided information to create compelling narratives that showcase specific contributions and their impact, organized by project. You follow instructions exactly and create substantive, impressive content."},
                {"role": "user", "content": prompt}
            ]
        )
        reflection = response.choices[0].message.content
        
        # Write to file
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        filename = f"Self_Reflection_Shopify_OS_C5_{today}.md"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(reflection)
        
        print(f"Self-reflection document created: {filepath}")
        return filepath
    except Exception as e:
        print(f"Error generating self-reflection: {e}")
        return None

# Main execution
def main():
    print("Starting PR Impact Analysis...")
    
    # Initialize clients
    github_client = initialize_github_client()
    openai_client = initialize_openai_client()
    
    # Comment out Google Drive client initialization
    # drive_service, docs_service = initialize_google_drive_client()
    
    # Read repository and author information from environment variables
    repo_names_str = os.getenv("GITHUB_REPO_NAMES", os.getenv("GITHUB_REPO_NAME", ""))
    author = os.getenv("GITHUB_AUTHOR", "")
    
    if not author:
        print("GITHUB_AUTHOR not found in environment variables. Please specify your GitHub username in the .env file.")
        return
    
    # Support multiple repositories by splitting the comma-separated string
    repo_names = [repo.strip() for repo in repo_names_str.split(",") if repo.strip()]
    
    if not repo_names:
        print("No repository names found. Please specify at least one repository in the .env file using GITHUB_REPO_NAMES or GITHUB_REPO_NAME.")
        return
    
    # Define specific date range (September 2024 to March 26, 2025)
    start_date = datetime.datetime(2024, 9, 1)  # September 1, 2024
    end_date = datetime.datetime(2025, 3, 26)   # March 26, 2025
    
    for repo_name in repo_names:
        print(f"\nAnalyzing repository: {repo_name}")
        
        # Create output directory for this repository
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        output_dir = create_output_directory(f"PR_Analysis_{repo_name.replace('/', '_')}_{author}_{today}")
        
        # Fetch and analyze PRs you authored
        authored_prs = fetch_prs(github_client, repo_name, start_date=start_date, end_date=end_date, 
                                author=author, merged_only=True)
        
        # Fetch and analyze PRs you reviewed
        reviewed_prs = fetch_prs_reviewed(github_client, repo_name, start_date=start_date, 
                                         end_date=end_date, reviewer=author)
        
        if not authored_prs and not reviewed_prs:
            print(f"No relevant PRs found in the specified time range for repository {repo_name}. Skipping.")
            continue
        
        # Analyze PRs and store results
        authored_analyses = []
        reviewed_analyses = []
        
        # Analyze authored PRs
        for pr in authored_prs:
            analysis = analyze_pr_impact(openai_client, pr, is_authored=True)
            file_path = write_pr_analysis_to_file(pr, analysis, output_dir)
            
            authored_analyses.append({
                'pr_data': pr,
                'analysis': analysis,
                'file_path': file_path
            })
            time.sleep(1)
        
        # Analyze reviewed PRs
        for pr in reviewed_prs:
            analysis = analyze_pr_impact(openai_client, pr, is_authored=False)
            file_path = write_pr_analysis_to_file(pr, analysis, output_dir)
            
            reviewed_analyses.append({
                'pr_data': pr,
                'analysis': analysis,
                'file_path': file_path
            })
            time.sleep(1)
        
        # Create brag doc summary
        summary_path = create_brag_doc_summary(authored_analyses, reviewed_analyses, repo_name, output_dir)
        
        print(f"\nAnalysis complete for {repo_name}! Brag document and individual PR analyses have been stored in: {output_dir}")
        print(f"Brag Doc summary: {summary_path}")
        
        if summary_path:
            reflection_path = generate_self_reflection(openai_client, summary_path, output_dir)
            if reflection_path:
                print(f"Self-reflection document: {reflection_path}")
            else:
                print("Failed to create self-reflection document.")

if __name__ == "__main__":
    main()
