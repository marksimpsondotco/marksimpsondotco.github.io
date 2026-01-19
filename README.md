# Price Drop Monitor - GitHub Pages

Live price monitoring dashboard hosted on GitHub Pages with automatic updates.

## 🌐 Live Demo

Once deployed, your dashboard will be available at:
`https://YOUR_USERNAME.github.io/YOUR_REPO/`

## ✨ Features

- 📱 **Mobile-friendly** responsive design
- 🔄 **Auto-refresh** every 5 minutes
- 🔍 **Search & filter** products and sites
- 📊 **Live statistics** dashboard
- 🤖 **Automated updates** via GitHub Actions (every 30 minutes)
- 🎨 **Beautiful UI** with gradient background

## 🚀 Quick Start

### 1. Create GitHub Repository

```bash
# Initialize git if not already done
git init
git branch -M main

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
```

### 2. Deploy to GitHub

```bash
./deploy_to_github.sh
```

This will:
- Export latest price drops to JSON
- Commit changes
- Push to GitHub

### 3. Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** → **Pages**
3. Source: **Deploy from a branch**
4. Branch: **main**, Folder: **/docs**
5. Click **Save**

Your site will be live in a few minutes!

## 📁 Project Structure

```
_generic/
├── docs/                      # GitHub Pages content
│   ├── index.html            # Main dashboard page
│   ├── styles.css            # Styling
│   ├── app.js                # JavaScript logic
│   └── price_drops.json      # Price data (auto-generated)
├── .github/
│   └── workflows/
│       └── update-prices.yml # Auto-update workflow
├── export_price_drops_json.py # Export script
├── deploy_to_github.sh       # Deployment script
└── sites/                    # Your monitoring data
```

## 🤖 Automatic Updates

GitHub Actions automatically updates your dashboard every 30 minutes:

1. Exports price drops from your logs
2. Commits updated JSON to the repository
3. GitHub Pages serves the new data

**Note**: GitHub Actions runs on their servers. Your `sites/` folder needs to be in the repository, or you'll need to modify the workflow to fetch data from your local machine.

## 🔧 Manual Update

To manually update the dashboard:

```bash
# Export data and deploy
./deploy_to_github.sh

# Or just export data locally
python export_price_drops_json.py sites docs/price_drops.json 100
```

## ⚙️ Configuration

### Update Frequency

Edit [.github/workflows/update-prices.yml](.github/workflows/update-prices.yml):

```yaml
on:
  schedule:
    - cron: '*/30 * * * *'  # Every 30 minutes
```

### Dashboard Refresh Rate

Edit [docs/app.js](docs/app.js):

```javascript
const REFRESH_INTERVAL = 300000; // 5 minutes in milliseconds
```

### Number of Price Drops

Edit the deployment script or workflow:

```bash
python export_price_drops_json.py sites docs/price_drops.json 100  # Last parameter
```

## 🎨 Customization

### Styling

Edit [docs/styles.css](docs/styles.css) to change colors, fonts, layout, etc.

### Branding

Edit [docs/index.html](docs/index.html) to change the title, header, or add your logo.

## 📊 Data Format

The `price_drops.json` file contains:

```json
{
  "generated_at": "2026-01-19T12:00:00",
  "total_drops": 150,
  "top_drops_shown": 100,
  "site_stats": [
    {
      "site": "example_com",
      "count": 10,
      "max_drop": 45.5,
      "total_savings": 250.00
    }
  ],
  "drops": [
    {
      "site": "example_com",
      "product": "Product Name",
      "percentage": 45.5,
      "old_price": "100.00",
      "new_price": "54.50",
      "timestamp": "2026-01-19T11:30:00",
      "url": "https://example.com/product"
    }
  ]
}
```

## 🔒 Security

- No API keys or passwords needed
- All data is public (it's on GitHub Pages)
- Don't commit sensitive data to the repository
- Consider using a private repository if your price data is confidential

## 🐛 Troubleshooting

**Dashboard shows "Error Loading Data"**
- Check that `price_drops.json` exists in the `docs/` folder
- Verify the file is valid JSON
- Check browser console for errors

**GitHub Actions failing**
- Ensure `sites/` folder is committed to the repository
- Check the Actions tab on GitHub for error logs
- Verify Python dependencies are correctly specified

**Changes not showing up**
- GitHub Pages can take 1-2 minutes to update
- Clear browser cache (Cmd+Shift+R)
- Check the JSON file was updated

## 📝 License

This project is for personal use. Modify as needed!

## 🆘 Support

Issues? Check:
1. Browser console for JavaScript errors
2. GitHub Actions logs for workflow errors
3. Ensure all files are committed and pushed
