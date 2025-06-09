# Wiki Image Display Troubleshooting

## The Issue
GitHub Wiki is not displaying the architecture diagram image, even though the image exists and is accessible.

## Solutions (in order of preference):

### 1. Direct Upload to Wiki (Recommended)
1. Go to Wiki → Edit
2. Drag and drop `docs/assets/architecture-2025.png` directly into the editor
3. Use the auto-generated filename: `![Architecture](architecture-2025.png)`

### 2. Use GitHub Issues Image Hosting
1. Create a new GitHub Issue
2. Drag the image into the issue description
3. Copy the generated GitHub image URL (starts with `user-images.githubusercontent.com`)
4. Use that URL in the Wiki

### 3. Use Alternative Markdown Syntax
Try this in the Wiki editor:
```markdown
## 🧠 Architecture Diagram

<img src="https://raw.githubusercontent.com/IgorGanapolsky/agent-web-scraper/main/docs/assets/architecture-2025.png" alt="AI-Powered Pain Discovery Pipeline" width="800">
```

### 4. Current Working Image URL
The image is confirmed accessible at:
https://raw.githubusercontent.com/IgorGanapolsky/agent-web-scraper/main/docs/assets/architecture-2025.png

### 5. Complete Wiki Content to Paste
Replace the entire Architecture Diagram section with:

```markdown
## 🧠 Architecture Diagram

![AI-Powered Pain Discovery Pipeline](https://raw.githubusercontent.com/IgorGanapolsky/agent-web-scraper/main/docs/assets/architecture-2025.png)

### Core Pipeline:
1. 📡 **Reddit Search** → via SerpAPI + scheduled scraping
2. 🧠 **Summarization** → GPT-4
3. 🟣 **Pain Point Extraction** → Gemini Pro
4. 📊 **Structuring & Charting** → JSON → LaTeX (PDFs) + CSV
5. 📧 **Delivery** → Email via Zoho SMTP + Formspree for inbound leads
6. 🌐 **Publishing** → GitHub Pages + Reports + Google Sheet log
```

## Next Steps
Try solution #1 first (direct upload), as it's the most reliable for GitHub Wiki.
