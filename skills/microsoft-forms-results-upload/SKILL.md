---
name: microsoft-forms-results-upload
description: Upload generated task result files to the Microsoft Forms URL configured for that task directory.
---

# Microsoft Forms Results Upload

Use this skill when the user asks to upload or submit files from a task's `results/`
directory to a Microsoft Form.

## Repository Convention

Each task that should support form upload stores its form URL in:

```text
<task-dir>/microsoft_form_url.txt
```

The first non-empty, non-comment line is the URL. Use this file to avoid asking for
the same task URL repeatedly. If the file is missing and the user gives a URL, save
that URL there before preparing the upload. If no URL is available, ask for it.

Generated input data belongs in `data/`; do not upload it unless the user explicitly
asks. Upload candidates are ordinary files under `results/`. Upload those result
files separately as individual file attachments. Do not create a zip, tarball, or
other archive unless the user explicitly asks for one.

## Workflow

1. Identify the intended task directory. If several task directories could match,
   ask which one.
2. Run `scripts/prepare_results_upload.py <task-dir>` to collect the form URL,
   result files, nickname, and validation warnings.
3. If there are no result files, stop and tell the user to generate results first.
4. If filenames do not begin with the task nickname, warn the user before upload.
5. Use browser automation when available to open the configured Microsoft Form and
   attach each discovered result file separately, preserving the original filename.
   Do not bundle the files into a zip or other archive unless the user explicitly
   asks for that.
6. Microsoft Forms file upload controls often require the user's signed-in browser
   session. If the form asks for login, account selection, MFA, or institutional
   credentials, pause and let the user complete that step. Do not ask for,
   store, or attempt to handle the user's password or MFA code.
7. Do not click a final Submit button or otherwise complete a live submission
   without explicit user approval immediately before that action.
8. After the upload attempt, report the task directory, form URL, uploaded files,
   and whether submission was completed or left ready for user review.

## Helper

`scripts/prepare_results_upload.py` is deterministic and has no network side
effects. It accepts:

```bash
python3 scripts/prepare_results_upload.py <task-dir>
python3 scripts/prepare_results_upload.py <task-dir> --url '<microsoft-form-url>'
```

With `--url`, it writes or replaces `<task-dir>/microsoft_form_url.txt` and then
prints a JSON summary. Without `--url`, it reads the saved URL if present.
