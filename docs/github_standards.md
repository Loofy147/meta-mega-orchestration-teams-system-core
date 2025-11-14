# Enterprise GitHub Standards: Meta Mega Orchestration Teams

This document outlines the foundational standards for all GitHub repositories managed by the Meta Mega Orchestration Teams. Adherence to these standards ensures consistency, scalability, security, and maintainability across all projects.

## 1. Repository Naming Convention

All repositories **MUST** adhere to a strict, three-part naming convention to ensure immediate clarity regarding the project's context, technology, and purpose.

**Format:** `<team-or-project>-<technology-stack>-<description>`

| Component | Description | Examples | Notes |
| :--- | :--- | :--- | :--- |
| **`<team-or-project>`** | Identifies the primary team or the overarching project. | `alpha-team`, `gamma-project`, `core-infra` | Must be a short, recognizable identifier. |
| **`<technology-stack>`** | The primary programming language or framework used. | `python`, `react`, `go`, `terraform`, `node` | Use lowercase and avoid abbreviations where possible. |
| **`<description>`** | A concise description of the repository's function. | `auth-service`, `data-pipeline`, `ui-components` | Should clearly state the purpose of the code. |

**Rules:**
1.  All characters **MUST** be lowercase.
2.  Components **MUST** be separated by a single hyphen (`-`).
3.  The full name **MUST** be descriptive yet concise.

**Example Names:**
*   `alpha-team-python-authentication-service`
*   `gamma-project-react-user-dashboard`
*   `core-infra-terraform-aws-network`

## 2. Branching Strategy

A hybrid branching strategy, combining the stability of Git Flow with the agility of GitHub Flow, is enforced via branch protection rules.

| Branch Name | Purpose | Protection Rules | Source Branch |
| :--- | :--- | :--- | :--- |
| **`main`** | **Production-Ready Code.** Represents the latest stable, deployed version. | **Strict:** Requires 2+ approvals, passing CI/CD status checks, and no force pushes. | `release/*` or `hotfix/*` |
| **`develop`** | **Integration Branch.** The latest integrated code for the next release cycle. | **Moderate:** Requires 1+ approval, passing CI status checks, and no force pushes. | `feature/*` |
| **`feature/*`** | **New Features/Changes.** Short-lived branches for all new development. | None (Ephemeral) | `develop` |
| **`release/*`** | **Release Preparation.** For final testing, bug fixes, and version bumping before production. | None (Ephemeral) | `develop` |
| **`hotfix/*`** | **Urgent Production Fixes.** For immediate fixes to the `main` branch. | None (Ephemeral) | `main` |

**Workflow:**
1.  All new work starts by branching from `develop` into a `feature/*` branch.
2.  Pull Requests (PRs) are opened from `feature/*` to `develop`.
3.  Once integrated and stable, `develop` is branched into `release/*`.
4.  The `release/*` branch is merged into both `main` and `develop` upon successful deployment.

## 3. Standard Directory Structure

Every new repository **MUST** be initialized with the following standardized structure to ensure immediate familiarity for all team members.

```
/
├── .github/
│ ├── ISSUE_TEMPLATE/
│ │ ├── bug_report.md
│ │ └── feature_request.md
│ └── workflows/
│ └── ci-cd.yml
├── docs/
├── src/
├── tests/
├── scripts/
├── .gitignore
└── README.md
```

| Directory/File | Purpose |
| :--- | :--- |
| **`.github/`** | Configuration for GitHub features (Actions, Templates, etc.). |
| **`ISSUE_TEMPLATE/`** | Standardized templates for bug reports and feature requests. |
| **`workflows/`** | GitHub Actions YAML files for CI/CD pipelines. |
| **`docs/`** | Comprehensive project documentation, architecture, and design decisions. |
| **`src/`** | The application's core source code. |
| **`tests/`** | All unit, integration, and end-to-end test files. |
| **`scripts/`** | Utility scripts for local development, deployment, or maintenance. |
| **`README.md`** | Project overview, setup instructions, and quick start guide. |

## 4. Governance and Automation Overview

### CI/CD Automation
All repositories will utilize **GitHub Actions** for Continuous Integration and Continuous Delivery. The standard `ci-cd.yml` workflow will include:
*   **Build:** Compiling the application.
*   **Test:** Running all tests in the `tests/` directory.
*   **Lint/Security Scan:** Performing static analysis for code quality and vulnerabilities.
*   **Deployment:** Automatic deployment upon merge to `main`.

### Repository Creation Automation
New repositories will be created using a dedicated automation script that leverages the GitHub API to:
1.  Create the repository with the correct name.
2.  Apply the standard directory structure.
3.  Configure the required branch protection rules for `main` and `develop`.
4.  Set up initial webhooks for external services.

This automation ensures that all new projects are compliant from the moment of creation.
