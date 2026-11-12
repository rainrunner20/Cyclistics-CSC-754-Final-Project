# Publish the repository

## GitHub CLI (recommended)

Requirements: Git and [GitHub CLI](https://cli.github.com/) installed on your machine. From the extracted project root:

```bash
gh auth login
git init -b main
git add .
git commit -m "chore: initialize Cyclistics research repository"
gh repo create cyclistics --public --source=. --remote=origin --push
```

If you want it private until you finish the class project, use `--private` instead of `--public`. If you already initialized Git, skip `git init`. The command creates a GitHub repository from the existing code and pushes the first commit. It may prompt you to authenticate.

## GitHub website alternative

Create a **blank** repository named `cyclistics` (do not initialize it with a README). Then:

```bash
git init -b main
git add .
git commit -m "chore: initialize Cyclistics research repository"
git remote add origin https://github.com/YOUR_USERNAME/cyclistics.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual username and authenticate if prompted.

## Finishing touches

- Check GitHub **Actions** after the first push; confirm the Python matrix and Docker checks actually pass.
- Suggested topics: `simulation`, `discrete-event-simulation`, `python`, `docker`, `devs`, `netlogo`, `agent-based-modeling`, `smart-cities`, `transportation`.
- Add a repository description from `PROJECT_DESCRIPTION.txt`.
- Once CI is verified, enable protection/rules for the `main` branch if desired.
- Only include screenshots of real running features, not placeholders that imply DEVSJAVA or NetLogo are finished.
