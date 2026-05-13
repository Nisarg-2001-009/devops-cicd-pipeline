# devops-cicd-pipeline

A production-grade, end-to-end CI/CD pipeline built with Jenkins, Docker, and GitHub. The project demonstrates automated testing, container image building, vulnerability scanning with Trivy, and zero-touch deployment — all triggered by a single `git push`.

> **Docker Hub:** [hub.docker.com/r/nisarg2001009/devops-cicd-pipeline](https://hub.docker.com/r/nisarg2001009/devops-cicd-pipeline)

---

## Table of Contents

1. [Architecture](#architecture)
2. [Tech Stack](#tech-stack)
3. [Prerequisites](#prerequisites)
4. [Setup & Running Locally](#setup--running-locally)
5. [Pipeline Stages](#pipeline-stages)
6. [Security Scanning](#security-scanning)
7. [Commit History Philosophy](#commit-history-philosophy)
8. [Lessons Learned](#lessons-learned)

---

## Architecture

The diagram below shows the full journey of a code change — from a developer's `git push` to a running container on the deploy host.

```
 Developer Workstation
 ┌──────────────────┐
 │   git push       │
 │   (feature/main) │
 └────────┬─────────┘
          │ HTTPS
          ▼
 ┌──────────────────┐        GitHub Webhook
 │                  │ ──────────────────────────────────────────┐
 │   GitHub Repo    │                                           │
 │                  │                                           │ POST /github-webhook/
 └──────────────────┘                                           │
                                                                ▼
                                                   ┌────────────────────────┐
                                                   │                        │
                                                   │   Jenkins Controller   │
                                                   │                        │
                                                   └────────────┬───────────┘
                                                                │
                                              ┌─────────────────▼──────────────────┐
                                              │         Declarative Pipeline        │
                                              │         (jenkins/Jenkinsfile)       │
                                              └─────────────────┬──────────────────┘
                                                                │
                          ┌─────────────────────────────────────┼──────────────────────────────────────┐
                          │                                      │                                      │
                          ▼                                      ▼                                      ▼
               ┌──────────────────┐               ┌─────────────────────────┐           ┌──────────────────────┐
               │  Stage 1         │               │  Stage 2                │           │  Stage 3             │
               │  Checkout        │──────────────▶│  Run Tests              │──────────▶│  Build Docker Image  │
               │  (checkout scm)  │               │  (pytest in venv)       │           │  (commit-hash tag)   │
               └──────────────────┘               └─────────────────────────┘           └──────────┬───────────┘
                                                                                                    │
                          ┌─────────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
               ┌──────────────────┐               ┌─────────────────────────┐           ┌──────────────────────┐
               │  Stage 4         │               │  Stage 5                │           │  Stage 6             │
               │  Security Scan   │──────────────▶│  Push to Docker Hub     │──────────▶│  Deploy              │
               │  (Trivy)         │               │  (:hash + :latest)      │           │  (docker run)        │
               └──────────────────┘               └─────────────────────────┘           └──────────┬───────────┘
                                                                                                    │
                                                                                                    ▼
                                                                                       ┌────────────────────────┐
                                                                                       │  Running Container     │
                                                                                       │  devops-cicd-app       │
                                                                                       │  localhost:5000        │
                                                                                       └────────────────────────┘

 Post-build (always)
 ┌──────────────────────────────────────────────────────────────┐
 │  docker logout  →  credentials purged from agent filesystem  │
 │  Console notification: SUCCESS or FAILURE with build URL     │
 └──────────────────────────────────────────────────────────────┘
```

**Data flows:**

| Flow | Transport | Notes |
|------|-----------|-------|
| Developer → GitHub | HTTPS / SSH | Standard Git push |
| GitHub → Jenkins | HTTP webhook (`/github-webhook/`) | Triggers pipeline on every push |
| Jenkins → Docker Hub | HTTPS | Image push after scan passes |
| Jenkins → Deploy host | Local Docker socket | `docker run` on the same host |
| End-user → App | HTTP on port 5000 | Flask REST API |

---

## Tech Stack

| Tool | Version | Role | Why it was chosen |
|------|---------|------|-------------------|
| **Python** | 3.11 | Application runtime | Mature ecosystem, excellent Flask and pytest support |
| **Flask** | Latest stable | REST API framework | Lightweight and explicit — no magic, no boilerplate |
| **pytest** | Latest stable | Test runner | First-class fixtures, concise assertions, rich plugin ecosystem |
| **Docker** | 24+ | Containerisation | Industry-standard image format; identical behaviour from laptop to prod |
| **Jenkins** | 2.4xx LTS | CI/CD controller | Self-hosted, Groovy-scriptable, huge plugin ecosystem; declarative pipelines are versionable alongside code |
| **Trivy** | Latest | Vulnerability scanner | Zero-config, scans OS packages and language deps, maintained by Aqua Security, native CI integration |
| **GitHub** | — | Source control & webhook source | Ubiquitous, free for public repos, native Jenkins webhook support |
| **Docker Hub** | — | Container registry | Free public registry; `docker pull` works everywhere without auth |
| **python-venv** | stdlib | Dependency isolation | Keeps build-agent Python clean; no pip conflicts between concurrent jobs |

---

## Prerequisites

Ensure the following are installed and accessible on your machine before proceeding.

| Prerequisite | Minimum version | Check |
|---|---|---|
| Docker Engine | 24.0 | `docker --version` |
| Docker Compose | 2.20 | `docker compose version` |
| Java (JDK) | 17 | `java -version` |
| Jenkins | 2.400 LTS | Running instance |
| Python | 3.11 | `python3 --version` |
| Trivy | 0.50 | `trivy --version` |
| Git | 2.40 | `git --version` |

**Jenkins plugins required:**

- Git
- Pipeline
- Credentials Binding
- Timestamper
- Blue Ocean (recommended for stage visualisation)

---

## Setup & Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/Nisarg-2001-009/devops-cicd-pipeline.git
cd devops-cicd-pipeline
```

### 2. Run the Flask app directly (no Docker)

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the development server
python app/app.py
```

The API is now available at `http://localhost:5000`. Test the endpoints:

```bash
curl http://localhost:5000/           # Welcome message
curl http://localhost:5000/health     # Health check
curl http://localhost:5000/api/info   # App metadata
```

### 3. Run the test suite

```bash
# With the venv activated (step 2)
pytest app/tests/ -v
```

Expected output:

```
app/tests/test_app.py::test_index_returns_200             PASSED
app/tests/test_app.py::test_index_contains_welcome_message PASSED
app/tests/test_app.py::test_health_returns_200            PASSED
app/tests/test_app.py::test_health_status_is_healthy      PASSED
app/tests/test_app.py::test_health_contains_timestamp     PASSED
app/tests/test_app.py::test_info_returns_200              PASSED
app/tests/test_app.py::test_info_app_name                 PASSED
app/tests/test_app.py::test_info_version                  PASSED
app/tests/test_app.py::test_info_default_environment      PASSED
app/tests/test_app.py::test_info_reads_app_env_variable   PASSED

10 passed in 0.XXs
```

### 4. Build and run with Docker

```bash
# Build the image from the repository root (build context = .)
docker build -t devops-cicd-pipeline:local -f docker/Dockerfile .

# Run the container
docker run -d \
  --name devops-cicd-app \
  -p 5000:5000 \
  devops-cicd-pipeline:local

# Verify
curl http://localhost:5000/health
```

### 5. Configure Jenkins

#### 5a. Store Docker Hub credentials

1. Navigate to **Manage Jenkins → Credentials → (global) → Add Credentials**
2. Kind: **Username with password**
3. Username: your Docker Hub username
4. Password: your Docker Hub access token (not your account password — create a token at hub.docker.com → Account Settings → Security)
5. ID: `dockerhub-credentials` ← must match exactly what the Jenkinsfile expects

#### 5b. Create the Pipeline job

1. **New Item → Pipeline**
2. Under **Build Triggers**, check **GitHub hook trigger for GITScm polling**
3. Under **Pipeline**, select **Pipeline script from SCM**
4. SCM: **Git** — enter your repository URL
5. Branch: `*/main`
6. Script Path: `jenkins/Jenkinsfile`
7. Save

#### 5c. Configure the GitHub webhook

1. Go to your GitHub repository → **Settings → Webhooks → Add webhook**
2. Payload URL: `http://<your-jenkins-host>:8080/github-webhook/`
3. Content type: `application/json`
4. Trigger: **Just the push event**
5. Save

From this point on, every `git push` to `main` triggers a full pipeline run automatically.

---

## Pipeline Stages

The pipeline is defined in `jenkins/Jenkinsfile` as a declarative pipeline. Every stage is independently visible in Jenkins' Blue Ocean UI, making it immediately obvious which phase failed and why.

### Stage 1 — Checkout

```
checkout scm
```

Retrieves source code from the SCM configured in the Jenkins job (branch, credentials, repository URL). Jenkins populates `GIT_COMMIT`, `GIT_BRANCH`, and `GIT_URL` automatically after this step. The `IMAGE_TAG` environment variable derives its value (`GIT_COMMIT.take(7)`) from `GIT_COMMIT`, so it becomes valid only after this stage completes.

**Why:** Decouples the pipeline definition from the repository URL — the job config owns that detail, not the `Jenkinsfile`. This means the same `Jenkinsfile` can be reused across forks without modification.

---

### Stage 2 — Run Tests

```
python3 -m venv .venv → pip install -r requirements.txt → pytest app/tests/ -v
```

Creates a fresh Python virtual environment in the workspace, installs all project dependencies from `requirements.txt`, then executes the full pytest test suite.

**Why run tests before building the image?**
Failing fast saves time and resources. A test failure costs seconds; building a Docker image, running Trivy, and then discovering the code is broken costs minutes and produces artefacts nobody will use.

**Why a virtual environment?**
The build agent may run many jobs simultaneously. Installing packages into a venv scopes them to this workspace, preventing version conflicts between concurrent builds and leaving the agent's system Python installation untouched.

**Test coverage:**

| Route | Tests |
|---|---|
| `GET /` | HTTP 200, `message` key present and non-empty |
| `GET /health` | HTTP 200, `status` = `"healthy"`, `timestamp` present |
| `GET /api/info` | HTTP 200, correct `app_name`, correct `version`, default and custom `APP_ENV` |

---

### Stage 3 — Build Docker Image

```
docker build -t nisarg2001009/devops-cicd-pipeline:<short-sha> -f docker/Dockerfile .
```

Builds the container image using the `Dockerfile` in `docker/`. The build context is the repository root (`.`) so `COPY` instructions can reach both `requirements.txt` and the `app/` directory.

**Image tag strategy — commit hash, not `:latest`:**
Every image is tagged with the 7-character short git SHA (e.g., `e6d9d4c`). This is an *immutable* tag — the same hash always refers to the same code. Immutable tags make:

- **Rollbacks trivial** — re-deploy the previous hash
- **Debugging simple** — `docker inspect` tells you exactly what code is inside
- **Audits reliable** — the registry is a complete, traceable history

**Dockerfile optimisations in `docker/Dockerfile`:**

| Technique | Benefit |
|---|---|
| `python:3.11-slim` base image | ~50% smaller than the full image; smaller attack surface |
| Dependency layer before source copy | `pip install` layer is cached; only invalidated when `requirements.txt` changes |
| `--no-cache-dir` on `pip install` | Removes downloaded package files after installation; smaller layer |
| Non-root `appuser` | Limits blast radius of any container escape; security best practice |
| `CMD` in exec form (JSON array) | Signals delivered directly to Python (PID 1); enables graceful shutdown |

---

### Stage 4 — Security Scan

See the dedicated [Security Scanning](#security-scanning) section below.

---

### Stage 5 — Push to Docker Hub

```
docker login --username ... --password-stdin
docker push nisarg2001009/devops-cicd-pipeline:<short-sha>
docker tag  nisarg2001009/devops-cicd-pipeline:<short-sha> nisarg2001009/devops-cicd-pipeline:latest
docker push nisarg2001009/devops-cicd-pipeline:latest
```

Authenticates with Docker Hub using credentials from the Jenkins Credential Store, then pushes two tags.

**Credential handling — `withCredentials` + `--password-stdin`:**
- `withCredentials` injects the username and password as environment variables and **automatically redacts them** in all Jenkins log output (replaced with `****`)
- `--password-stdin` reads the password from stdin rather than a CLI argument — CLI arguments are visible in the process list (`ps aux`) and in shell history files

**Two tags — why both?**

| Tag | Purpose |
|---|---|
| `:<short-sha>` | Immutable. Use in production manifests, Helm charts, Terraform. Guarantees reproducibility. |
| `:latest` | Mutable. Useful for `docker pull` scripts, local development, and humans who just want "the newest image." Never use in production deployments. |

---

### Stage 6 — Deploy

```
docker stop devops-cicd-app  || true
docker rm   devops-cicd-app  || true
docker run -d --name devops-cicd-app -p 5000:5000 --restart unless-stopped \
    nisarg2001009/devops-cicd-pipeline:<short-sha>
```

Stops and removes the previously running container (if any), then starts a fresh one from the newly pushed image.

**Key flags explained:**

| Flag | Reason |
|---|---|
| `|| true` on stop/rm | Makes the first deployment (when no container exists yet) succeed instead of failing |
| `-d` | Detached mode — Jenkins step returns immediately; the container keeps running |
| `--name devops-cicd-app` | Fixed name allows subsequent pipelines to reliably stop/replace this exact container |
| `-p 5000:5000` | Maps host port 5000 to Flask's listening port inside the container |
| `--restart unless-stopped` | Container auto-restarts on crash or host reboot; only stays down if explicitly stopped by an operator |
| Image pinned to `:<short-sha>` | Deploys exactly the image built and scanned in this run — not whatever `:latest` happened to be |

**Note:** For production workloads, replace this stage with an orchestrator call (`kubectl rollout`, `docker service update`, `aws ecs update-service`) to gain rolling updates, health-check gating, and automatic rollback.

---

### Post-build Actions

The `post` block in the Jenkinsfile runs unconditionally after all stages, regardless of outcome.

**`always` — credential cleanup:**

```bash
docker logout || true
```

Docker writes credentials to `~/.docker/config.json` on the agent filesystem after `docker login`. Logging out purges that file immediately. Without this, credentials would persist between builds and across unrelated jobs running on the same agent — a meaningful security risk in shared CI environments.

**`success` — notification:**

Logs a formatted summary to the Jenkins console including image tag, container name, endpoint URL, branch, and full commit SHA. In a team environment, replace with `slackSend`, a GitHub status check, or a webhook to your monitoring platform.

**`failure` — notification:**

Logs a formatted failure summary including the build URL, branch, and commit SHA so engineers can navigate directly to the failing build from a notification without hunting through the Jenkins dashboard.

---

## Security Scanning

### Why Trivy?

[Trivy](https://trivy.dev) is an open-source, all-in-one vulnerability scanner maintained by Aqua Security. It was chosen over alternatives for these reasons:

| Criterion | Trivy | Snyk | Clair |
|---|---|---|---|
| Zero configuration | Yes | Requires account | No |
| Scans OS packages | Yes | Yes | Yes |
| Scans language deps | Yes (pip, npm, etc.) | Yes | No |
| Free for CI use | Yes (fully open-source) | Limited free tier | Yes |
| CI integration | Single binary, exit codes | Plugin/CLI | Complex setup |
| Actively maintained | Yes | Yes | Limited |

### How the scan works

The pipeline runs Trivy **twice** in Stage 4:

```
Pass 1 (informational):  --exit-code 0  --severity UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL
Pass 2 (policy gate):    --exit-code 1  --severity CRITICAL
```

**Pass 1** always exits with code 0 regardless of findings. Its purpose is to display the complete vulnerability landscape in the Jenkins log — engineers can see every LOW, MEDIUM, and HIGH finding without the build aborting.

**Pass 2** exits with code 1 (causing Jenkins to mark the build as FAILURE and halt the pipeline) if any CRITICAL CVE is found. This prevents a critically vulnerable image from ever reaching the Docker Hub registry.

Splitting into two passes means: on failure, the full picture is still visible in the log. A single scan with `--exit-code 1` would surface only the CRITICAL findings, hiding lower-severity context.

### CVE severity levels

CVSS (Common Vulnerability Scoring System) assigns each CVE a score from 0 to 10. Trivy maps scores to severity labels as follows:

| Severity | CVSS Score | Pipeline action | Typical example |
|---|---|---|---|
| **CRITICAL** | 9.0 – 10.0 | **Fails the build** | Remote code execution, unauthenticated full system compromise |
| **HIGH** | 7.0 – 8.9 | Reported, build continues | Privilege escalation, significant data exposure |
| **MEDIUM** | 4.0 – 6.9 | Reported, build continues | Requires local access or specific conditions |
| **LOW** | 0.1 – 3.9 | Reported, build continues | Minor information disclosure |
| **UNKNOWN** | Unscored | Reported, build continues | CVE exists but score not yet assigned |

### Responding to CRITICAL findings

If Trivy fails the build:

1. Check the **Pass 1 output** in the Jenkins log for the full CVE list and affected package names.
2. Update the relevant package in `requirements.txt` (Python deps) or rebuild from a newer base image (`FROM python:3.11-slim` → pull a newer digest) to pick up patched OS packages.
3. Re-push — Jenkins will re-run the scan automatically.

---

## Commit History Philosophy

This project follows the [Conventional Commits](https://www.conventionalcommits.org/) specification. Every commit message is structured as:

```
<type>(<optional scope>): <short description>

<optional longer body>
```

**Types used in this project:**

| Type | When to use |
|---|---|
| `feat` | A new feature or capability (pipeline stage, route, test) |
| `fix` | A bug fix |
| `chore` | Housekeeping — scaffolding, `.gitkeep` removal, dependency bumps |
| `docs` | Documentation only |
| `refactor` | Code restructured with no behaviour change |
| `test` | Adding or updating tests with no production code change |
| `ci` | Changes to the CI/CD pipeline itself |

**Why conventional commits?**

1. **Machine-readable** — tools like `semantic-release` can automatically determine the next semver version and generate changelogs from commit messages alone.
2. **Scannable history** — `git log --oneline` becomes a meaningful audit trail rather than a wall of "fix stuff" messages.
3. **Scope control** — the optional scope field (`feat(api): ...`) lets reviewers immediately understand which part of the system changed.
4. **Team alignment** — a shared convention eliminates subjective debates about commit message style in code review.

**Example from this project's log:**

```
e6d9d4c feat: update root endpoint welcome message to include version
b3f08ea feat: add declarative Jenkinsfile with 6-stage CI/CD pipeline
f4d1152 feat: add Dockerfile with multi-layer caching and non-root user
41f1b6e feat: add pytest unit tests for all API endpoints
fe23900 feat: add Flask REST API with health and info endpoints
c39c009 chore: initialise project folder structure with app, docker, and jenkins directories
```

---

## Lessons Learned

### 1. Build context placement matters more than it looks

The `docker build` command's final argument — the build context — determines what the Docker daemon can see during the build. The `Dockerfile` lives in `docker/`, but `COPY requirements.txt .` needs to reach a file at the repository root. Passing `.` (workspace root) as the context and `-f docker/Dockerfile` to name the file explicitly is the only clean solution that doesn't require moving either the `Dockerfile` or `requirements.txt`.

### 2. Credential cleanup is not optional in shared CI environments

It is easy to treat `docker logout` as an afterthought. It is not. In a shared Jenkins environment where multiple jobs run on the same agent, a lingering `~/.docker/config.json` is a credential leak waiting to happen. Running cleanup unconditionally in `post { always { ... } }` ensures it fires even on build failure — which is exactly when you most want it, because failures can leave the workspace in an indeterminate state.

### 3. Two Trivy passes give better signal than one

The intuitive approach is a single `trivy image --exit-code 1 --severity CRITICAL`. The problem: on failure, the log shows only CRITICAL entries. Running a pass with `--exit-code 0` first prints the full picture; the second pass enforces the gate. Engineers can see the complete vulnerability landscape rather than being shown only the blocking CVEs, which is valuable context when deciding whether to patch, update the base image, or accept a risk.

### 4. Immutable image tags make CI/CD trustworthy

Tagging images with the git commit hash (`IMAGE_TAG = GIT_COMMIT.take(7)`) creates a permanent, verifiable link between source code and deployable artefact. This is the foundation of safe rollbacks, reliable audits, and reproducible builds. The `:latest` tag is pushed as a convenience but should never be the tag referenced in deployment manifests.

### 5. Declarative pipelines belong in source control

Storing the `Jenkinsfile` in the repository alongside the code it builds means pipeline changes go through the same pull-request review process as application code. A broken pipeline change is caught before it merges. The history of pipeline evolution is visible in `git log`. No CI/UI clicks are required to reproduce the exact pipeline state at any historical commit.

### 6. `--restart unless-stopped` is not the same as always-restart

Docker's `--restart always` policy restarts a container even if an operator explicitly ran `docker stop` — the container comes back on the next Docker daemon restart. `unless-stopped` respects an explicit stop: once an operator stops the container, it stays stopped across reboots. This is the correct policy for a manually managed single-host deployment where operators need to be able to stop the service for maintenance without it coming back unexpectedly.

---

## Docker Hub

The published image is available at:

**[hub.docker.com/r/nisarg2001009/devops-cicd-pipeline](https://hub.docker.com/r/nisarg2001009/devops-cicd-pipeline)**

Pull the latest build:

```bash
docker pull nisarg2001009/devops-cicd-pipeline:latest
```

Pull a specific commit:

```bash
docker pull nisarg2001009/devops-cicd-pipeline:<short-sha>
```

---

## Project Structure

```
devops-cicd-pipeline/
├── app/
│   ├── app.py              # Flask application factory and routes
│   ├── __init__.py
│   └── tests/
│       ├── conftest.py     # pytest fixtures (Flask test client)
│       └── test_app.py     # Unit tests for all three routes
├── docker/
│   └── Dockerfile          # Multi-stage optimised image definition
├── jenkins/
│   └── Jenkinsfile         # Declarative 6-stage CI/CD pipeline
├── requirements.txt        # Python runtime and test dependencies
└── README.md
```

---

*Built by [Nisarg](https://github.com/Nisarg-2001-009)*
