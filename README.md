# hammad.dev — machine learning notes and portfolio

This repository contains a static website in the `docs/` folder. GitHub Pages can publish that folder directly from this repository.

- No external database, visitor accounts, or website upload dashboard.
- Blog posts and portfolio entries are Markdown files stored in this GitHub repository.
- Small images can also be stored here. Videos and large model files should stay on YouTube or Hugging Face and be linked from the site.
- The site is public after GitHub Pages is enabled. Do not add passwords, private data, or API keys to the repository.

The name **hammad.dev** is the website’s brand. The free GitHub Pages address for this repository is expected to be <https://hammad-naeem1.github.io/fieldnotes/>. That address is not a custom `hammad.dev` domain.

## Publish the site the first time

First, commit and push these changes to the `main` branch of `hammad-naeem1/fieldnotes`. Then:

1. Open <https://github.com/hammad-naeem1/fieldnotes>.
2. Click **Settings** near the top of the repository. If it is hidden, open the repository’s **…** menu and choose **Settings**.
3. In the left menu, click **Pages**.
4. Under **Build and deployment**, set **Source** to **Deploy from a branch**.
5. For the branch, choose **main**. For the folder, choose **/docs**.
6. Click **Save**.
7. On that Pages settings screen, wait for GitHub to show the live link. Open it to see the site.

GitHub Pages is free for public repositories on GitHub Free. It rebuilds the site when you push changes to the selected branch. The repository must stay public for this free setup. GitHub documents the current setup in [Configuring a publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

## Add a blog post from GitHub

You can create a post in the GitHub website; you do not need to edit the website itself or use a special writing app.

1. Open the `fieldnotes` repository on GitHub.
2. Click **Add file**, then **Create new file**.
3. In the filename box, enter a path like `docs/_posts/2026-10-09-my-first-ml-project.md`. Use the post date in `YYYY-MM-DD` format and a short lowercase title.
4. Paste this at the top, then replace the example words with your own:

   ```yaml
   ---
   title: "My first ML project"
   date: 2026-10-09 12:00:00 +0500
   description: "What I tried, what happened, and what I learned."
   categories: [learning]
   ---
   ```

5. Leave a blank line after the last `---`, then write the post. Use `##` before a section heading, `-` for a bullet, and `[words to click](https://example.com)` for a link.
6. Scroll down. Under **Commit changes**, write a short message such as `Add first ML project article` and select **Commit directly to the main branch**.
7. Click **Commit changes**. GitHub Pages will publish it after its build finishes. Check the **Actions** tab if you want to see the publishing status.

New posts belong in `docs/_posts/`. The homepage and Blog page list them automatically.

## Add a portfolio project

1. In the repository, choose **Add file → Create new file**.
2. Name it `docs/_projects/house-price-prediction.md` (replace the last part with a short project name).
3. Copy the starter fields from [`docs/_templates/new-project.md`](docs/_templates/new-project.md). Replace the example links with your project’s real links. Delete a link line if you do not have that page yet.
4. Write what problem you worked on, what you built, what you learned, and what you would improve.
5. Commit the file to `main`. It will appear on **My Portfolio** after GitHub Pages rebuilds.

Use the `huggingface_url` field to link to a model or demo on the [CodeWithHammad Hugging Face profile](https://huggingface.co/CodeWithHammad), and `github_url` for the source code. The website shows the project description and links; it does not host or run the model.

## Add an image

For a small screenshot or chart, open `docs/assets/images/` in GitHub and choose **Add file → Upload files**. If you upload from the top of the repository, make sure the file ends up in that folder. Commit the image, then include it in a Markdown post like this:

```markdown
![A short description of the chart]({{ '/assets/images/my-chart.png' | relative_url }})
```

Do not put large videos or model weights in this repository. Link videos from their video page and host model files or demos on Hugging Face. GitHub Pages has published-site size and bandwidth limits; see [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits).

## Contact links on the site

- Email: `hammadconnect1@gmail.com`
- GitHub: [hammad-naeem1](https://github.com/hammad-naeem1)
- Hugging Face: [CodeWithHammad](https://huggingface.co/CodeWithHammad)
- Discord name: `hammad-naeem1` (shown as text; a Discord username alone is not a public profile link)

No Reddit link is shown yet because a Reddit username or profile link has not been provided.

## About the other files in this repository

The root of this repository still contains files from the earlier Django/Render prototype. The GitHub Pages setup above publishes only `docs/`; those older server files are not needed for this static site. Follow the steps in this README for publishing and updating the public website.
