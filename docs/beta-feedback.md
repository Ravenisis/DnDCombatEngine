# Beta Feedback

GitHub issue creation is currently restricted, so public beta feedback should
flow through **Help > Report Bug**.

## Current Workflow

When the app is running from a source checkout, submitted bug reports are
appended to `BETA_TESTER_REPORTS.md` in the repository root.

When the app is running from an installed build, it may not have permission to
write back into the installed application folder or the GitHub repository. In
that case, the same markdown report format is written beside the app's writable
data folder so it can be copied into the repo later.

## Token-Backed Options

When you are ready to generate a token for automated repo submission, the safest
options are:

- Fine-grained GitHub token with access to only `Ravenisis/DnDCombatEngine` and
  repository `Contents: Read and write`, used to append to `BETA_TESTER_REPORTS.md`.
- Fine-grained GitHub token with `Contents: Read and write` and `Pull requests:
  Read and write`, used to write reports on a beta-feedback branch and open a
  pull request.
- GitHub Actions `workflow_dispatch` token flow, where the app sends a minimal
  report payload to a manually approved workflow instead of writing directly.

Do not store a personal access token in source control. Prefer an environment
variable such as `DND_COMBAT_ENGINE_GITHUB_TOKEN` or a local user setting stored
outside the repository.
