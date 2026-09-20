# User-submitted media

Sources: [issue #6: Images for use and evidence](https://github.com/project-owner/stay-up/issues/6)
and [issue #7: Vid](https://github.com/project-owner/stay-up/issues/7).
The [README gallery](../README.md#user-submitted-images-and-videos) uses the original GitHub attachments.
No application capture feature produced these documentation additions.

## Images from issue #6

| Attachment | Description from visual inspection | Limit |
|---|---|---|
| [9dd17192](https://example.invalid/removed-media) | Photograph of a Windows sign-in screen with an RSA SecurID prompt. | No established timing or causal relationship to the helper. |
| [2d9cc158](https://example.invalid/removed-media) | Rust window showing `idle 00:03:43`, with terminal windows beside it. | A single visible reading, not proof of continuous observation. |
| [48a572b0](https://example.invalid/removed-media) | Wider desktop view showing `idle 00:05:17` and two mostly blank terminal windows. | Window ownership was not verified from the photograph. |
| [699f84fc](https://example.invalid/removed-media) | Rust window showing `idle 00:10:38`, with the same visual arrangement. | Does not establish uninterrupted power, lock, or input-state coverage. |

These photos support the visual-refresh discussion.
They do not establish that the helper caused or prevented a lock.
Process identifiers and timer values are historical, not settings.

## Videos from both issues

| Source | Attachment | Container duration |
|---|---|---|
| Issue #6 | [Video 1: 026dbf2b](https://example.invalid/removed-media) | About 19.94 seconds |
| Issue #6 | [Video 2: f9bf4b8c](https://example.invalid/removed-media) | About 8.21 seconds |
| Issue #7 | [Video 1: cba1ad29](https://example.invalid/removed-media) | About 8.54 seconds |
| Issue #7 | [Video 2: 1630e4a0](https://example.invalid/removed-media) | About 8.21 seconds |

Authenticated GitHub CLI requests retrieved all four videos.
The container brand is QuickTime. Duration comes from the movie header, not playback review.
Video playback was not available in this review environment.
This review makes no frame-by-frame or audio claims.
The two 8.21-second files have different SHA-256 hashes. The table retains both source links.

Issue #6 also contains `![Uploading 655339016...]` without a completed attachment URL.
That placeholder is not usable media and is not included in the README gallery.

## Access and publication limits

Authenticated GitHub CLI requests retrieved all eight completed attachments.
An unauthenticated request for the first image returned HTTP 404.
This review did not establish public access or inline video playback.
Use the source issue links if the README renderer does not show an attachment.
The README provides direct video links rather than promising an embedded player.

Photos include account or desktop context unrelated to the application.
They remain linked to the originals at the user's request.
Review and redact that context before wider public distribution.
The sign-in photo appears in a collapsed contextual section, not as the product preview.

Media stays on GitHub. These changes add no binary media to Git.
Authenticated downloads used for inspection remain under ignored `local/issue-media-review/`.
Historical media and capture-probe evidence remain separate from current record-only application logging.
