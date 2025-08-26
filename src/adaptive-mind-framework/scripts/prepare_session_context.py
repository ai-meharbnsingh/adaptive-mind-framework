# -*- coding: utf-8 -*-
import os
import subprocess
import argparse
import logging
import json
from typing import Optional, Dict, Any
from pathlib import Path
import datetime  # Import for timestamping the output file

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the root directory of your project
# Assumes the script is in PROJECT_ROOT/scripts/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# --- Configuration Management ---
def load_config() -> Dict[str, Any]:
    """Load configuration from file with fallback to defaults."""
    config_path = Path(PROJECT_ROOT) / "config" / "context_config.json"
    default_config = {
        'max_changelog_lines': 200,
        'git_pull_timeout_seconds': 60,
        'git_rev_parse_timeout_seconds': 30,
        'supported_phases': list(range(0, 7)),  # Phases 0 to 6
        'required_files': ['context_summary.md', 'changelog.md'],
        'include_ai_output_summaries': False,
        'ai_output_summary_lines': 50,
        'default_output_filename': 'session_context_latest.md'  # New config for default output file
    }

    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                default_config.update(user_config)
                logging.info(f"Loaded configuration from {config_path}")
        except json.JSONDecodeError:
            logging.warning(f"Invalid JSON in config file {config_path}. Using defaults.")
        except Exception as e:
            logging.warning(f"Could not load config file {config_path}: {e}. Using defaults.", exc_info=True)
    else:
        logging.info(f"Config file not found at {config_path}. Using default configuration.")

    return default_config


# Load configuration globally for the script
CONFIG = load_config()


# --- NEW FUNCTION TO INSERT HERE (already present in the last provided full code block, verifying placement) ---
def validate_phase_num(phase_num: Optional[int]) -> bool:
    """
    Validates the given phase number is within the expected range
    defined in CONFIG['supported_phases']. Handles None gracefully.
    """
    if phase_num is None:
        return True

    if not isinstance(phase_num, int):
        logging.error(f"Validation Error: Phase number must be an integer, got {type(phase_num).__name__}.")
        return False

    # Check against supported_phases from CONFIG
    if phase_num not in CONFIG['supported_phases']:
        logging.error(
            f"Validation Error: Phase number {phase_num} is not in the supported range {CONFIG['supported_phases']}.")
        return False

    return True


# --- END NEW FUNCTION INSERTION ---


# --- Path Validation ---
def is_safe_path(filepath: str) -> bool:
    """Enhanced path validation with symlink resolution to prevent path traversal."""
    try:
        # Resolve to real path to handle symlinks
        real_project_root = os.path.realpath(PROJECT_ROOT)
        real_filepath = os.path.realpath(filepath)

        # Check if the real path starts with the real project root
        return real_filepath.startswith(real_project_root)
    except (OSError, ValueError) as e:
        logging.error(f"Error resolving real path for {filepath}: {e}", exc_info=True)
        return False


# --- Git Operations ---
def get_latest_github_url() -> str:
    """Fetches the GitHub remote URL and current branch."""
    try:
        repo_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=PROJECT_ROOT,
            timeout=CONFIG['git_rev_parse_timeout_seconds']
        ).decode('utf-8').strip()

        current_branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=PROJECT_ROOT,
            timeout=CONFIG['git_rev_parse_timeout_seconds']
        ).decode('utf-8').strip()

        if repo_url.endswith('.git'):  # Remove .git suffix for cleaner URL
            repo_url = repo_url[:-4]
        return f"{repo_url}/tree/{current_branch}"
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        error_msg = f"Git command failed: {e}"
        logging.error(error_msg)
        return f"Error getting GitHub URL: {error_msg}. Please provide manually."
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        logging.error(error_msg, exc_info=True)
        return f"Error getting GitHub URL: {error_msg}. Please provide manually."


def update_repository() -> bool:
    """Update repository with proper git commands, handling errors and timeouts."""
    logging.info("Attempting to pull latest changes from GitHub...")
    try:
        current_branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=PROJECT_ROOT,
            timeout=CONFIG['git_rev_parse_timeout_seconds']
        ).decode('utf-8').strip()

        if not current_branch:
            logging.error("Could not determine current Git branch. Cannot pull.")
            return False

        subprocess.run(
            ["git", "pull", "origin", current_branch],
            check=True,
            cwd=PROJECT_ROOT,
            timeout=CONFIG['git_pull_timeout_seconds']
        )
        logging.info("Successfully pulled latest changes.")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(
            f"Git update failed (CalledProcessError): Command '{' '.join(e.cmd)}' returned non-zero exit status {e.returncode}. Output: {e.stderr.decode('utf-8').strip()}")
        return False
    except subprocess.TimeoutExpired as e:
        logging.error(
            f"Git update failed (TimeoutExpired): Command '{' '.join(e.cmd)}' timed out after {e.timeout} seconds.")
        return False
    except FileNotFoundError:
        logging.error("Git command not found. Please ensure Git is installed and in your PATH.")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred during git update: {e}", exc_info=True)
        return False


def get_git_status() -> Dict[str, Any]:
    """Get comprehensive git status information."""
    try:
        status_output = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=PROJECT_ROOT,
            timeout=10
        ).decode('utf-8').strip()

        return {
            'has_uncommitted_changes': bool(status_output),
            'status_output': status_output,
            'is_clean': not bool(status_output),
            'error': None
        }
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        logging.warning(f"Could not get git status: {e}")
        return {'has_uncommitted_changes': None, 'is_clean': None, 'error': str(e)}
    except Exception as e:
        logging.warning(f"An unexpected error occurred while getting git status: {e}", exc_info=True)
        return {'has_uncommitted_changes': None, 'is_clean': None, 'error': str(e)}


# --- File Reading ---
def read_file_content(filepath: str, max_lines: Optional[int] = None) -> str:
    """Safely reads content from a file with optional line limiting."""
    if not is_safe_path(filepath):
        logging.error(f"Security warning: Attempted to read unsafe path: {filepath}")
        return f"--- Security Warning: Attempted to read file outside project root or unsafe path: {filepath} ---"

    try:
        if not os.path.exists(filepath):
            logging.warning(f"File not found: {filepath}")
            return f"--- File not found: {filepath} ---"

        with open(filepath, 'r', encoding='utf-8') as f:
            if max_lines:
                lines = []
                for i, line in enumerate(f):
                    lines.append(line.rstrip())  # rstrip to remove trailing newlines before truncation check
                    if i >= max_lines - 1:  # -1 because enumerate starts from 0
                        lines.append("... (truncated for brevity)")
                        break
                return '\n'.join(lines)
            return f.read()
    except UnicodeDecodeError:
        logging.error(f"Error: {filepath} contains non-UTF-8 content or invalid characters.", exc_info=True)
        return f"--- Error: {filepath} contains non-UTF-8 content ---"
    except PermissionError:
        logging.error(f"Error: Permission denied reading {filepath}.", exc_info=True)
        return f"--- Error: Permission denied reading {filepath} ---"
    except Exception as e:
        logging.error(f"An unexpected error occurred reading {filepath}: {e}", exc_info=True)
        return f"--- Error reading {filepath}: {e} ---"


# --- Context Preparation ---
def prepare_context(phase_num: Optional[int] = None) -> str:
    """
    Prepares the comprehensive context string for the AI assistant.
    phase_num: Optional, specific phase number to include its README.
    """
    context_parts = []

    # Input validation for phase_num
    if not validate_phase_num(phase_num):
        logging.error(f"Invalid phase number provided: {phase_num}. Skipping phase-specific README.")
        phase_num = None  # Reset to None if invalid to prevent further errors

    # 1. General Project Files
    context_parts.append("# ✨ Project Context for Adaptive Mind\n\n")
    context_parts.append("## 📄 Core Project Files\n")

    # context_summary.md
    context_parts.append("### context_summary.md:\n```markdown\n")
    context_parts.append(read_file_content(os.path.join(PROJECT_ROOT, "context_summary.md")))
    context_parts.append("\n```\n")

    # changelog.md
    context_parts.append("### changelog.md (Last few entries):\n```markdown\n")
    changelog_content = read_file_content(os.path.join(PROJECT_ROOT, "changelog.md"),
                                          max_lines=CONFIG['max_changelog_lines'])
    context_parts.append(changelog_content)
    context_parts.append("\n```\n")

    # 2. Phase-specific README
    if phase_num is not None:
        readme_path = os.path.join(PROJECT_ROOT, "docs", f"README_phase{phase_num}.md")
        context_parts.append(f"## 📚 Phase {phase_num} Documentation (README_phase{phase_num}.md):\n```markdown\n")
        context_parts.append(read_file_content(readme_path))
        context_parts.append("\n```\n")

    # 3. AI Output Summaries (Optional, requires more complex logic)
    if CONFIG['include_ai_output_summaries']:
        logging.info("Including AI Output Summaries...")
        # This would involve reading `ai_output` files and summarizing them.
        # For now, it's a placeholder.
        context_parts.append("## 🤖 Recent AI Output Summaries:\n")
        # Placeholder for future implementation:
        # for ai_dir in ['chatgpt_output', 'gemini_output', 'claude_output']:
        #     ai_output_path = os.path.join(PROJECT_ROOT, 'ai_output', ai_dir)
        #     if os.path.exists(ai_output_path):
        #         recent_files = sorted([f for f in os.listdir(ai_output_path) if os.path.isfile(os.path.join(ai_output_path, f))], reverse=True)[:5] # Get last 5 files
        #         for filename in recent_files:
        #             file_content = read_file_content(os.path.join(ai_output_path, filename), max_lines=CONFIG['ai_output_summary_lines'])
        #             context_parts.append(f"### {ai_dir}/{filename}:\n```\n{file_content}\n```\n")
    else:
        logging.info("Skipping AI Output Summaries as per configuration.")

    return "".join(context_parts)


# --- Main Execution ---
def main():
    parser = argparse.ArgumentParser(description="Prepare project context for AI assistant.")
    parser.add_argument('--phase', type=int, help="Include README for a specific phase (e.g., --phase 1).")
    # New argument for output file
    parser.add_argument('--output-file', type=str,
                        default=CONFIG['default_output_filename'],
                        help="Path to save context output (relative to project root). Default: session_context_latest.md")  # Updated help text
    args = parser.parse_args()

    # 1. Ensure local Git repo is up-to-date
    if not update_repository():
        user_choice = input("Git update failed. Continue with potentially outdated context? (y/N): ")
        if user_choice.lower() != 'y':
            logging.info("Context preparation cancelled by user.")
            return
        logging.warning("Continuing with potentially outdated repository state.")

    # 2. Compile Context
    compiled_context_body = prepare_context(args.phase)

    # 3. Add GitHub URL to the compiled context
    github_url = get_latest_github_url()

    final_output_content = (
        "🧠 CONTEXT:\n"
        f"{compiled_context_body}\n"
        "📦 GITHUB:\n"
        f"{github_url}\n"
    )

    # 4. Save to output file with safety measures
    output_filepath = Path(PROJECT_ROOT) / args.output_file

    # Security: Validate output path to prevent writing outside project root or to critical system paths
    if not is_safe_path(str(output_filepath.resolve())):  # Resolve to absolute path before checking safety
        logging.error(f"Security Error: Attempted to write context to an unsafe path: {output_filepath}")
        print(f"\n================================================================================\n")
        print(f"ERROR: Cannot save context to unsafe path. Please copy from console output below:\n")
        print(f"================================================================================\n")
        print(final_output_content)
        print(f"\n================================================================================\n")
        print(f"Please copy the output above and paste it into the AI chat.\n")
        print(f"================================================================================\n")
        return  # Exit if path is unsafe

    try:
        # Create parent directories if they don't exist
        output_filepath.parent.mkdir(parents=True, exist_ok=True)

        # Warn if file exists and will be overwritten
        if output_filepath.exists():
            logging.warning(f"Output file '{output_filepath.name}' already exists and will be overwritten.")

        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(final_output_content)
        logging.info(f"Compiled context saved to: {output_filepath}")
        print(f"\n================================================================================\n")
        print(f"Context compiled and saved to: {output_filepath}\n")
        print(f"Please copy the content from this file and paste it into the AI chat.\n")
        print(f"================================================================================\n")
    except Exception as e:
        logging.error(f"Failed to write context to file {output_filepath}: {e}", exc_info=True)
        print(f"\n================================================================================\n")
        print(f"ERROR: Failed to save context to file. Please copy from console output below:\n")
        print(f"================================================================================\n")
        # Fallback to printing if file write fails
        print(final_output_content)
        print(f"\n================================================================================\n")
        print(f"Please copy the output above and paste it into the AI chat.\n")
        print(f"================================================================================\n")

    # Optional: Display Git Status
    git_status = get_git_status()
    if git_status['error']:
        print(f"\n--- Git Status Error: {git_status['error']} ---")
    else:
        print("\n--- Current Git Status ---")
        if git_status['has_uncommitted_changes']:
            print("WARNING: You have uncommitted changes in your repository!")
            print(git_status['status_output'])
        else:
            print("Your working directory is clean.")
        print("--------------------------")


if __name__ == "__main__":
    main()