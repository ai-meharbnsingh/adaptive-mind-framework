# Phase 0: AI Ops Bootstrap Layer (Project Memory, Prompt Recovery, GitHub Sync)

This document outlines the foundational processes and tools for the "Adaptive Mind" project's AI Operations (AI Ops) memory system. The goal of Phase 0 is to ensure continuous context for all AI collaborators (Gemini, Claude, ChatGPT), minimize memory loss across sessions, and enable efficient, data-driven evolution of the entire system.

By adhering to this workflow, we build a robust, antifragile collaboration environment that prevents "context drift" and allows for seamless resumption of complex tasks.

---

## 🚀 Project Memory Workflow: The Heart of AI Ops

The following components are critical for maintaining the project's memory and enabling intelligent collaboration:

1.  **`context_summary.md`**:
    *   **Purpose:** This file acts as the compressed, high-level memory from the previous day's (or session's) work. It synthesizes key decisions, progress, roadblocks, and next steps into a concise summary.
    *   **Usage:** At the start of every new session, the content of `context_summary.md` will be pasted directly into the AI prompt as `🧠 CONTEXT:`, ensuring the AI immediately grasps the current state of the project.
    *   **Maintenance:** This file will be updated (and potentially summarized by an AI) at the end of each significant work session.

2.  **GitHub Repository**:
    *   **Purpose:** The GitHub repository (`https://github.com/ai-meharbnsingh/adaptive-mind.git`) serves as the definitive source of truth for the entire codebase and project files.
    *   **Usage:** All code changes, documentation updates, and file additions must be committed and pushed to GitHub regularly.
    *   **Synchronization:** Before starting a session, always ensure your local repository is synced with the latest GitHub changes (`git pull`).

3.  **Module-Specific `README.md` files (e.g., `antifragile_framework/README.md`)**:
    *   **Purpose:** Each major module or component of the "Adaptive Mind" system will have its own `README.md`. These READMEs will detail the module's purpose, architecture, key functionalities, and important implementation notes.
    *   **Usage:** These READMEs should be updated to reflect significant contributions made by specific AI agents (e.g., "Feature X developed with Gemini," "Refinement Y suggested by Claude"). This provides clear attribution and a high-level overview of AI impact.

4.  **`ai_output/{ai_name}/` Directories**:
    *   **Purpose:** These directories (`ai_output/chatgpt_output/`, `ai_output/gemini_output/`, `ai_output/claude_output/`) are dedicated logging locations for *all* AI-generated content during a session.
    *   **Usage:** Every substantial piece of AI output – code snippets, detailed explanations, architecture diagrams (as text/markdown), debugging logs, problem-solving discussions – must be saved here, typically as timestamped or session-ID'd markdown files.
    *   **Importance:** This serves as an auditable trail of AI contributions and provides raw material for `context_summary.md` generation and future learning.

---

## 💡 On Session Start: The Intelligent Hand-off

At the beginning of each new AI collaboration session, I will provide the following inputs, enabling you (the Project Setup & Documentation Assistant) to provide the most relevant and contextualized guidance:

*   **`🧠 CONTEXT:`** → The content of the latest `context_summary.md`.
*   **`📦 GITHUB:`** → The URL of the latest GitHub repository state.

Upon receiving these, you will perform the following actions to prepare for the session:

1.  **Code Change Analysis:**
    *   Identify and analyze the latest code changes in the GitHub repository since the last session.
    *   Summarize the key deltas, new files, modified functionalities, and resolved issues.
2.  **Documentation Update Suggestions:**
    *   Propose updates to `context_summary.md` to reflect new progress, decisions, or changes that need to be carried forward.
    *   Suggest new entries for `changelog.md` for significant milestones, feature additions, or major bug fixes.
    *   Recommend specific updates to relevant module `README.md` files, especially regarding AI contributions.
3.  **Next Prompt Generation:**
    *   Based on open goals, identified gaps from the context, or new insights from code analysis, suggest highly targeted prompts for Gemini or Claude to continue the development process.
4.  **Architectural & Automation Ideas:**
    *   As the codebase evolves, suggest potential refactoring, new file organizations, or automation opportunities (e.g., for testing, deployment, or AI Ops tasks themselves).

---

## 🛠️ Initial Setup & Local Repository Structure

To begin, follow these steps to set up your local environment and establish the Phase 0 structure:

1.  **Clone the GitHub Repository:**
    ```bash
    git clone https://github.com/your-username/adaptive-mind.git
    cd adaptive-mind
    ```
    *Note: You have already done this step.*
2.  **Create Python Virtual Environment:**
    ```bash
    python -m venv .venv
    # On Windows:
    .venv\Scripts\activate
    # On macOS/Linux:
    source .venv/bin/activate
    ```
3.  **Create Core Project Memory Files:**
    ```bash
    touch README.md
    touch context_summary.md
    touch changelog.md
    ```
    *Note: You have already done this step.*
4.  **Create AI Output Directories:**
    ```bash
    mkdir -p ai_output/chatgpt_output
    mkdir -p ai_output/gemini_output
    mkdir -p ai_output/claude_output
    ```
    *Note: You have already done this step.*
5.  **Create Documentation Directories and this README:**
    ```bash
    mkdir -p docs
    # Save the content of this document into docs/README_phase0.md
    ```
    *Note: You have already done this step (mkdir docs). Now you are saving this content into the file.*
6.  **Create Scripts Directory:**
    ```bash
    mkdir scripts
    ```
    *Note: You have already done this step.*
7.  **Install Essential Libraries (as per main strategy document):**
    ```bash
    pip install openpyxl requests Flask psycopg2-binary SQLAlchemy PyYAML docker pytest scikit-learn numpy pandas openai anthropic google-generativeai
    ```
8.  **Initial Git Commit:**
    ```bash
    git add .
    git commit -m "Initialize Phase 0: AI Ops Bootstrap Layer with project memory workflow"
    git push origin main # Or your main branch name
    ```
    *Note: You have done the initial commit for your directory structure. We will commit these new files at the end of this current session.*

---