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

The first time **Help > Report Bug** is used, the app offers to save a
fine-grained GitHub token. On Windows, that token is encrypted for the current
Windows user with DPAPI and stored under the app's local settings directory. It
is never written to the repository or displayed back in Preferences. Once saved,
future reports automatically append to the repository through the GitHub
Contents API. The token can be replaced or cleared under **Settings >
Preferences**.

If the online submission fails because of network access, token permissions, or
a GitHub error, the report is still saved to the local markdown file. The
`DND_COMBAT_ENGINE_GITHUB_TOKEN` environment variable remains available as an
administrative override and takes precedence over the saved token.

Supported environment variables:

- `DND_COMBAT_ENGINE_GITHUB_TOKEN`: fine-grained token used for online bug report
  submission.
- `DND_COMBAT_ENGINE_BUG_REPORT_REPO`: target repository, default
  `Ravenisis/DnDCombatEngine`.
- `DND_COMBAT_ENGINE_BUG_REPORT_BRANCH`: target branch, default `main`.
- `DND_COMBAT_ENGINE_BUG_REPORT_PATH`: target report file, default
  `BETA_TESTER_REPORTS.md`.

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

Do not store a personal access token in source control. Create a dedicated
fine-grained token limited to `Ravenisis/DnDCombatEngine`, grant only repository
`Contents: Read and write`, and enter it through the app's token prompt or
Preferences screen.
