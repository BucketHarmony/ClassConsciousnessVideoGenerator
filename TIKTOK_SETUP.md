# TikTok Publishing Setup Guide

This guide explains how to set up automatic TikTok publishing for AI Ken Burns videos.

## Overview

The AI Ken Burns generator can automatically publish videos to TikTok using browser automation. This requires exporting cookies from your browser after logging into TikTok.

## Prerequisites

- Google Chrome browser (recommended)
- A TikTok account
- A browser extension for exporting cookies

## Step 1: Install Cookie Export Extension

Install one of these browser extensions:

### Chrome
- **Cookie-Editor** (Recommended): [Chrome Web Store](https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm)
- **Get cookies.txt LOCALLY**: [Chrome Web Store](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)

### Firefox
- **Cookie-Editor**: [Firefox Add-ons](https://addons.mozilla.org/en-US/firefox/addon/cookie-editor/)
- **cookies.txt**: [Firefox Add-ons](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

### Edge
- **Cookie-Editor**: [Edge Add-ons](https://microsoftedge.microsoft.com/addons/detail/cookie-editor/neaplmfkghagebokkhpjpoebhdledlfi)

## Step 2: Log into TikTok

1. Open your browser and go to [tiktok.com](https://www.tiktok.com)
2. Log into your TikTok account
3. Make sure you can access your profile and upload page

## Step 3: Export Cookies

### Using Cookie-Editor (Recommended)

1. While on tiktok.com, click the Cookie-Editor extension icon
2. Click the **Export** button (download icon)
3. Select **JSON** format
4. Save the file as `tiktok_cookies.json`

### Using Get cookies.txt LOCALLY

1. While on tiktok.com, click the extension icon
2. Click **Export**
3. Save as `cookies.txt`
4. Rename to `tiktok_cookies.json` (the tool will auto-detect format)

## Step 4: Place Cookies File

Save your exported cookies file to one of these locations:

| Location | Description |
|----------|-------------|
| `~/.tiktok_cookies.json` | User home directory (recommended) |
| `./tiktok_cookies.json` | Current working directory |
| Custom path | Set `TIKTOK_COOKIES_PATH` environment variable |

### Windows Example
```
C:\Users\YourName\.tiktok_cookies.json
```

### Mac/Linux Example
```
/home/yourname/.tiktok_cookies.json
```

### Using Environment Variable
```bash
# Windows (PowerShell)
$env:TIKTOK_COOKIES_PATH = "C:\path\to\cookies.json"

# Mac/Linux
export TIKTOK_COOKIES_PATH="/path/to/cookies.json"
```

## Step 5: Verify Setup

Run the setup verification command:

```bash
ai-ken-burns tiktok-setup
```

You should see:
```
[OK] TikTok cookies found: /path/to/tiktok_cookies.json
You're ready to publish videos!
```

## Usage

### Generate and Publish in One Command

```bash
# Generate TikTok-ready vertical video and publish
ai-ken-burns generate --resolution tiktok --publish

# With AI-generated images only
ai-ken-burns generate --resolution tiktok --ai-images-only --publish

# See the browser during upload (for debugging)
ai-ken-burns generate --resolution tiktok --publish --publish-visible
```

### Publish an Existing Video

```bash
# Basic publish
ai-ken-burns publish video.mp4 -d "My documentary about labor history"

# With custom hashtags
ai-ken-burns publish video.mp4 -d "History repeats" --hashtags "history,labor,documentary"

# Show browser window (useful for debugging)
ai-ken-burns publish video.mp4 -d "Test upload" --visible

# Use specific cookies file
ai-ken-burns publish video.mp4 -d "My video" --cookies /path/to/cookies.json
```

## Cookie File Format

The cookies file should be a JSON array containing cookie objects:

```json
[
  {
    "name": "sessionid",
    "value": "abc123...",
    "domain": ".tiktok.com",
    "path": "/",
    "secure": true,
    "httpOnly": true
  },
  {
    "name": "tt_webid",
    "value": "xyz789...",
    "domain": ".tiktok.com",
    "path": "/"
  }
]
```

The most important cookie is `sessionid` - this authenticates your TikTok session.

## Troubleshooting

### "No TikTok cookies file found"

- Verify the cookies file exists in one of the expected locations
- Check file permissions
- Try setting the `TIKTOK_COOKIES_PATH` environment variable explicitly

### "Upload failed" or Browser Errors

1. **Re-export cookies**: TikTok cookies expire after ~2 months
2. **Check TikTok login**: Make sure you're still logged in on tiktok.com
3. **Try visible mode**: Run with `--visible` to see what's happening
4. **Check video format**: TikTok prefers MP4 with H.264 codec

### "sessionid cookie not found"

- Make sure you exported cookies while logged into TikTok
- Try logging out and back in, then re-export
- Use a different cookie export extension

### Browser Issues

- Make sure Google Chrome is installed
- The tool uses Selenium WebDriver which auto-downloads ChromeDriver
- Try updating Chrome to the latest version

## Important Notes

### Cookie Expiration

TikTok session cookies typically expire after **2 months**. You'll need to:
1. Log into TikTok in your browser
2. Re-export the cookies
3. Replace your old cookies file

Set a reminder to refresh cookies periodically!

### Rate Limits

TikTok may rate-limit uploads. Best practices:
- Don't upload more than a few videos per hour
- Space out automated uploads
- Vary your content and descriptions

### Content Guidelines

All uploaded content must comply with [TikTok's Community Guidelines](https://www.tiktok.com/community-guidelines). The AI Ken Burns generator creates educational documentary content about labor history.

### Privacy

- Keep your cookies file secure - it provides access to your TikTok account
- Don't share or commit your cookies file to version control
- The `.gitignore` already excludes common cookie file names

## Default Hashtags

When using `--publish` with `generate`, these default hashtags are added:
- #history
- #classconsciousness
- #laborhistory
- #workers
- #documentary
- #learnontiktok
- #historytiktok

You can override with custom hashtags using the `publish` command.

## Support

If you encounter issues:
1. Run `ai-ken-burns tiktok-setup` to check configuration
2. Try `--visible` mode to see the browser
3. Check that your cookies are fresh (re-export if needed)
4. Verify TikTok isn't blocking automated uploads
