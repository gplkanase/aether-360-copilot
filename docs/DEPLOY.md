# Deploy Aether 360 publicly

No secrets are required for the local Streamlit demo. The app runs on synthetic CSVs bundled in the repo.

Do not put GitHub tokens, Snowflake passwords, or `.streamlit/secrets.toml` in this repository or in email attachments.

## 1. Publish code + demo video to GitHub

```powershell
git remote add origin https://github.com/<your-user>/aether-360-copilot.git
git push -u origin main
```

Attach `docs/demo/Aether360-demo.mp4` to a GitHub release `v1.0.0` if judges should download it.

### Public URLs after publish

| Asset | URL |
| --- | --- |
| Repository | `https://github.com/<your-user>/aether-360-copilot` |
| Demo video (release) | `https://github.com/<your-user>/aether-360-copilot/releases/download/v1.0.0/Aether360-demo.mp4` |
| Raw video | `https://raw.githubusercontent.com/<your-user>/aether-360-copilot/main/docs/demo/Aether360-demo.mp4` |

## 2. Live app on Streamlit Community Cloud (optional)

1. Sign in at [https://share.streamlit.io/](https://share.streamlit.io/) with GitHub.
2. **New app** → your `aether-360-copilot` repo, branch `main`.
3. Main file path: `streamlit_app.py` (repo root).

## 3. Snowflake (optional, for full CoCo demo)

Connect CoCo to Snowflake and run `sql/00_setup.sql` through `sql/11_validation.sql` as described in `README.md`.
