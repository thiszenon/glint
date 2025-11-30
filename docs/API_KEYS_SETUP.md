# Glint API Keys Setup Guide (Optional)

## 🎯 Do You Need API Keys?

**NO!** Glint works perfectly **out-of-the-box** without any API keys.

However, if you're a power user who:
- Fetches trends very frequently (every few minutes)
- Watches many topics (10+)
- Hits rate limits

...then you can optionally add your own API keys for higher limits.

---

## 📊 Rate Limits (Without API Keys)

| Source | Public Limit | With API Key |
|--------|-------------|--------------|
| GitHub | 60 req/hour | 5,000 req/hour |
| Reddit | Works fine | Higher limits |
| HackerNews | No limit | No limit |
| Dev.to | 10 req/sec | Higher limits |
| Product Hunt | RSS (no limit) | N/A |

**For most users, public limits are enough!**

---

## 🔑 How to Add API Keys

### Step 1: Get Your API Keys

#### GitHub Personal Access Token
1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name (e.g., "Glint")
4. **No scopes needed** (leave all checkboxes unchecked for public repos)
5. Click "Generate token"
6. **Copy the token** (you won't see it again!)

#### Reddit API Credentials
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Fill in:
   - **Name**: Glint
   - **Type**: Select "script"
   - **Redirect URI**: http://localhost:8080
4. Click "Create app"
5. **Copy**:
   - Client ID (under the app name)
   - Secret (next to "secret")

#### Dev.to API Key
1. Go to https://dev.to/settings/extensions
2. Click "Generate API Key"
3. Give it a description (e.g., "Glint")
4. **Copy the key**

---

### Step 2: Add Keys to Glint

Open your terminal and run:

```bash
# GitHub
glint config secrets set github_token YOUR_GITHUB_TOKEN_HERE

# Reddit
glint config secrets set reddit_client_id YOUR_REDDIT_CLIENT_ID
glint config secrets set reddit_secret YOUR_REDDIT_SECRET

# Dev.to
glint config secrets set devto YOUR_DEVTO_KEY
```

**Example:**
```bash
glint config secrets set github_token ghp_abc123xyz789...
```

---

### Step 3: Verify

Check that your keys are saved:

```bash
glint config secrets show
```

You'll see:
```
API Keys
┌────────────────────┬──────────────┐
│ Key                │ Value        │
├────────────────────┼──────────────┤
│ github_token       │ ghp_****     │
│ reddit_client_id   │ abc1****     │
│ reddit_secret      │ xyz9****     │
│ devto              │ dev_****     │
└────────────────────┴──────────────┘
```

---

### Step 4: Test

Run a fetch to see if it works:

```bash
glint fetch
```

If you see trends, you're all set! 🎉

---

## 🔒 Security Notes

- Keys are stored locally in `~/.glint/config.json`
- **Never share your config.json file**
- Keys are only used by your local Glint installation
- No data is sent to any external servers (except the APIs you're fetching from)

---

## ❌ Removing API Keys

If you want to remove a key:

```bash
glint config secrets set github_token ""
```

Or manually edit `~/.glint/config.json` and delete the key.

---

## 🆘 Troubleshooting

**"Invalid token" error:**
- Make sure you copied the entire token (no spaces)
- For GitHub, regenerate the token if it expired

**Still hitting rate limits:**
- Check your fetch frequency (don't fetch more than once every 15-30 minutes)
- Reduce the number of topics you're watching

**Keys not working:**
- Run `glint config secrets show` to verify they're saved
- Check the logs: `cat ~/.glint/glint.log`
