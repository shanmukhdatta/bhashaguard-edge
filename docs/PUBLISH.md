# Publishing this repository

Suggested name: `bhashaguard-edge`.

Suggested description: `Offline evidence review and script checks for Indian-language AI responses, with a Snapdragon deployment plan.`

The complete application and submission files are in this tree. The repository is ready to publish, but only a successfully created remote repository gives you a real GitHub URL for the Unstop form. Do not submit a placeholder or a link to someone else's repository.

If the delivered archive includes `bhashaguard-edge.bundle`, restore the committed repository with:

```bash
git clone bhashaguard-edge.bundle bhashaguard-edge
cd bhashaguard-edge
```

With GitHub CLI already installed and authenticated to your intended account:

```bash
gh auth status
gh repo create bhashaguard-edge --public --source=. --remote=origin --push
gh repo view --web
```

Choose public visibility only if you intend the code and documents to be publicly accessible. A private repository needs a judge-access arrangement that you verify with the organizer. Do not upload private data or model weights.

If the name already exists, inspect that repository before choosing a new name. Do not overwrite another project or force-push. After publication, verify that the README, application code, tests and submission documents are visible, and check the CI result. Paste the repository's actual URL into Unstop.

The initial local commit uses an explicit build-assistant identity rather than inventing the participant's Git identity. This does not assert legal ownership of the participant's research. The project owner can set the desired author attribution before publishing.
