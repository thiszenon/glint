# API Keys Configuration 🔐

Glint is designed to respect your privacy and provide a seamless experience right out of the box. While **API keys are not required** for standard usage, adding them can enhance your experience by increasing rate limits for high-frequency updates.

---

## 🎯 Why Use API Keys?

By default, Glint uses public APIs which have strict rate limits. If you find yourself hitting these limits (e.g., when watching many topics), adding your own credentials will grant you significantly higher quotas.

### Comparison Table

| Source | Public Access (Anonymous) | With API Key |
| :--- | :--- | :--- |
| **GitHub** | 60 requests / hour | 5,000 requests / hour |
| **Reddit** | Restricted / Varying | High / Dedicated |
| **Dev.to** | 10 requests / second | Higher dedicated limits |
| **HackerNews** | Unlimited (Public API) | N/A |

---

## 🔑 Source Configuration Guide

Follow these steps to generate keys for each source.

### 🐙 GitHub
1. Go to your [GitHub Token Settings](https://github.com/settings/tokens).
2. Click **Generate new token (classic)**.
3. **Important**: You do not need any special scopes for public repo data. Just give it a name like "Glint Watch".
4. Copy the generated `ghp_...` token.

### 🤖 Reddit
1. Visit the [Reddit App Preferences](https://www.reddit.com/prefs/apps).
2. Click **Create another app...** at the bottom.
3. Set a name ("Glint"), select **script**, and set the redirect URI to `http://localhost:8080`.
4. You will need both the **Client ID** (short string under the app name) and the **Secret**.

### 💻 Dev.to
1. Navigate to your [Dev.to Extensions Settings](https://dev.to/settings/extensions).
2. Under "DEV Community API Keys", generate a new key named "Glint".
3. Copy the generated key.

---

## 🛠️ Applying Keys via CLI

Once you have your keys, use the `glint config` command to save them securely to your local configuration.

### Deployment Commands
```bash
# Set GitHub Token
glint config secrets set github_token YOUR_GITHUB_TOKEN

# Set Reddit Credentials
glint config secrets set reddit_client_id YOUR_CLIENT_ID
glint config secrets set reddit_secret YOUR_SECRET

# Set Dev.to Key
glint config secrets set devto YOUR_DEVTO_KEY
```

### Verification
To check which keys are currently configured (values are masked for security):
```bash
glint config secrets show
```

---

## �️ Security & Privacy

> [!IMPORTANT]
> Your API keys are stored **exclusively on your local machine** within your user profile directory (`~/.glint/`). Glint never transmits these keys to any server other than the respective source providers' official APIs.

---

## 🆘 Troubleshooting

- **Invalid Token Error**: Ensure you haven't copied extra spaces or newline characters.
- **Rate Limit Hits anyway**: Some sources (like Reddit) have stricter rules for new accounts. Ensure your app is set to "script" type.
- **Key not saving**: Make sure you have initialized Glint first using `glint init`.

---

[⬅️ Back to README](../README.md)
