# ExamTrack v4 — automatic exam-source monitoring

Static frontend + scheduled GitHub Actions monitor.

## What is automatic?
- `monitor.py` checks each official source once per day.
- It stores a SHA-256 hash so source changes are detected.
- It extracts obvious date strings when possible.
- It NEVER replaces a known exam date just because a random date appeared on a page.
- Ambiguous changes are written to `monitor-report.json` for review.
- When `exams.json` changes, GitHub Actions commits it. Vercel/Netlify can redeploy from the repository automatically.

## Deploy
1. Put the contents of this folder in a GitHub repository.
2. Import that repository into Vercel or Netlify.
3. Keep GitHub Actions enabled.
4. The workflow runs daily at 02:17 UTC and can also be run manually from Actions.

## Important limitation
Official exam sites are inconsistent. Some publish dates in PDFs/images or behind dynamic portals. This monitor therefore uses conservative extraction rather than guessing. For high-value exams such as GATE/UPSC, keep the official links and verify notifications before applying.
