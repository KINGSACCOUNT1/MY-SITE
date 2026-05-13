# Cloudflare Bot Protection Configuration Guide

## Step 1: Enable Bot Fight Mode (Free Plan)

1. Log into Cloudflare Dashboard
2. Select your domain: **elitewealthcapita.uk**
3. Go to **Security** > **Bots**
4. Enable **Bot Fight Mode** (Free)
   - This automatically challenges suspicious bots
   - Allows legitimate search engines (Google, Bing, etc.)

## Step 2: Create Firewall Rules

Go to **Security** > **WAF** > **Firewall Rules**

### Rule 1: Block Known Security Scanners

**Name:** Block Security Scanners  
**Expression:**
```
(http.user_agent contains "scamadviser") or
(http.user_agent contains "sitecheck") or
(http.user_agent contains "norton") or
(http.user_agent contains "mcafee") or
(http.user_agent contains "wpscan") or
(http.user_agent contains "nikto") or
(http.user_agent contains "nessus") or
(http.user_agent contains "qualys") or
(http.user_agent contains "sqlmap") or
(http.user_agent contains "metasploit")
```
**Action:** Block

### Rule 2: Block AI Crawlers (Not Google)

**Name:** Block AI Scrapers  
**Expression:**
```
(http.user_agent contains "gptbot") or
(http.user_agent contains "chatgpt") or
(http.user_agent contains "ccbot") or
(http.user_agent contains "anthropic") or
(http.user_agent contains "claude-web") or
(http.user_agent contains "cohere") or
(http.user_agent contains "bytespider") or
(http.user_agent contains "petalbot")
```
**Action:** Block

### Rule 3: Block SEO Scrapers (Not Google/Bing)

**Name:** Block SEO Scrapers  
**Expression:**
```
(http.user_agent contains "semrush") or
(http.user_agent contains "ahrefs") or
(http.user_agent contains "mj12bot") or
(http.user_agent contains "blexbot") or
(http.user_agent contains "dataforseo") or
(http.user_agent contains "screaming frog")
```
**Action:** Block

### Rule 4: Challenge Suspicious Bots

**Name:** Challenge Suspicious Activity  
**Expression:**
```
(cf.client.bot) and not (cf.verified_bot_category in {"Search Engine Crawler"})
```
**Action:** Managed Challenge (JS Challenge)

## Step 3: Rate Limiting

Go to **Security** > **Rate Limiting Rules**

**Name:** Limit Automated Requests  
**Expression:** All incoming requests  
**Rate:** 100 requests per 10 seconds  
**Action:** Block

## Step 4: Enable Additional Security Features

1. **Under Attack Mode** (Emergency only)
   - Security > Settings > Security Level > "I'm Under Attack"
   
2. **Browser Integrity Check**
   - Security > Settings > Enable "Browser Integrity Check"

3. **Challenge Passage**
   - Security > Settings > Set to "30 minutes"

4. **Security Level**
   - Set to "Medium" or "High"

## Step 5: Allow Legitimate Bots

Go to **Security** > **Bots** > **Configure**

Make sure these are ALLOWED:
- ✅ Googlebot
- ✅ Bingbot  
- ✅ Verified Crawlers
- ✅ Good Bots

## Verification

After configuration:
1. Test your site from normal browser (should work)
2. Test with curl: `curl -A "ScamAdviser" https://elitewealthcapita.uk` (should be blocked)
3. Monitor in Cloudflare **Analytics** > **Security**

## Notes

- These rules will block malicious scanners at Cloudflare level (before hitting your server)
- Google and legitimate search engines will still be able to crawl
- Your site will remain in Google search results
- Monitor blocked traffic in Cloudflare dashboard
