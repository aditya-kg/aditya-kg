# Setup

This is a complete GitHub profile README kit for **Aditya Kumar Guru** (`aditya-kg`).

The repository should be:

```text
https://github.com/aditya-kg/aditya-kg
```

That repository's `README.md` is what GitHub displays on the profile page.

---

## 1. Push the files

Copy the contents of this folder into your `aditya-kg/aditya-kg` repository.

```bash
git add -A
git commit -m "upgrade profile README"
git push
```

The repository must be **public** because the README references SVG assets stored in the repository.

---

## 2. Enable GitHub Actions write permissions

Go to:

**Settings → Actions → General → Workflow permissions**

Select:

**Read and write permissions**

and save.

This allows the Radar, Metrics and Snake workflows to write generated SVGs back to the repository.

---

## 3. Add the Metrics token

The `lowlighter/metrics` workflow needs a token to access contribution/profile data.

Create a GitHub token and add it as:

```text
METRICS_TOKEN
```

under:

**Settings → Secrets and variables → Actions → New repository secret**

The workflow uses this secret for the Metrics jobs.

---

## 4. Run the workflows once

Go to the repository's **Actions** tab and manually run:

| Workflow | Generates |
|---|---|
| **Metrics** | contribution calendar, language breakdown, achievements |
| **Charts and cards** | research radar, GitHub language radar, stats card, project cards |
| **Snake** | contribution snake on the `output` branch |

After the first successful runs, the README will start showing the generated assets.

---

## 5. Local radar

The research radar is controlled by:

```text
assets/skills.json
```

Values are profile-focus scores from 0–100, not GitHub measurements.

Regenerate it with:

```powershell
python scripts\radar.py --data assets\skills.json -o assets\radar
```

---

## 6. Project cards

Featured repositories are controlled by:

```text
assets/projects.json
```

The workflow fetches live stars, forks and primary language information from GitHub.

To regenerate locally:

```powershell
python scripts\cards.py --user aditya-kg --projects assets\projects.json --out assets
```

If you run locally without a GitHub token, the cards still render but contribution/streak tiles may be omitted.

---

## 7. Snake

The Snake workflow publishes its generated SVGs to the `output` branch.

The README references:

```text
https://raw.githubusercontent.com/aditya-kg/aditya-kg/output/
```

So the snake will show only after the first successful Snake workflow run.

---

## 8. Portrait

The README currently uses your GitHub avatar directly:

```text
https://github.com/aditya-kg.png?size=512
```

This avoids shipping someone else's portrait in the template.

If you later want the dot-matrix portrait effect, place your own image in the repo and run `scripts/dotify.py` to generate `assets/portrait.svg`.
