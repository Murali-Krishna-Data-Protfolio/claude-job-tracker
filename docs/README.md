# NeetiFusion

Marketing site for NeetiFusion, an AI-era data consulting enterprise.

This site lives in `docs/` inside the `claude-job-tracker` repository (unrelated
to the job tracker app itself) so it can use GitHub's built-in "deploy from
`/docs`" Pages option with no extra setup.

## Structure

```
docs/
├── index.html    # markup only
├── css/style.css # all styles
└── js/app.js     # hero network animation + reduced-motion handling
```

## Deploying

No build step and no dependencies beyond Google Fonts — everything else is relatively linked.

**GitHub Pages (this repo)**
1. Go to Settings → Pages in the `claude-job-tracker` repository
2. Under "Build and deployment", set Source to "Deploy from a branch"
3. Choose the branch this was pushed to, folder `/docs`, then Save
4. The site will be live at `https://murali-krishna-data-protfolio.github.io/claude-job-tracker/`

**Netlify / Vercel**
Import this repository and set the "publish directory" / "root directory" to `docs` — no build command needed.

**Custom domain**
Once deployed on any of the above, add your domain (e.g. `neetifusion.com`) in that host's domain settings and point its DNS to the host as instructed there.
