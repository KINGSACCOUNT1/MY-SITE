# ============================================
# ADD DATABASE_URL TO ELITE-WEALTH-CAPITA
# ============================================

# Set environment
$env:HOME = $env:USERPROFILE
$env:RENDERCLI_APIKEY = "rnd_sQgRXPau93UpdZAmnBQ4JsqkOZxU"
$RENDER_CLI = "E:\DailyFundzProfile\Downloads\render-windows-x86_64.exe"

Write-Host "`n===================================================" -ForegroundColor Cyan
Write-Host "  RENDER CLI - ADD DATABASE_URL TO ELITE-WEALTH" -ForegroundColor Yellow
Write-Host "===================================================" -ForegroundColor Cyan

# Step 1: Ask for database URL
Write-Host "`n📋 STEP 1: Get Database URL" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Go to Render Dashboard and find your PostgreSQL database URL from:"
Write-Host "  • kasikornbank service (BANK project)"
Write-Host "  • consignment-site service (CONSIGNMENT-SITE project)"
Write-Host "  • Or any other PostgreSQL database" -ForegroundColor Yellow
Write-Host ""
Write-Host "The URL looks like:" -ForegroundColor Cyan
Write-Host "  postgresql://user:password@host.render.com:5432/dbname" -ForegroundColor DarkGray
Write-Host ""

$DATABASE_URL = Read-Host "Paste your DATABASE_URL here"

if ([string]::IsNullOrWhiteSpace($DATABASE_URL)) {
    Write-Host "`n❌ ERROR: No DATABASE_URL provided!" -ForegroundColor Red
    Write-Host "Run this script again and paste your database URL." -ForegroundColor Yellow
    exit 1
}

# Step 2: Add environment variable using Render Dashboard URL
Write-Host "`n📤 STEP 2: Adding DATABASE_URL to elite-wealth-capita..." -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray

Write-Host "`n⚠️  IMPORTANT:" -ForegroundColor Yellow
Write-Host "The Render CLI doesn't support adding environment variables directly."
Write-Host "I've copied your DATABASE_URL to clipboard."
Write-Host ""
Write-Host "Please follow these steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Go to: https://dashboard.render.com/web/srv-d72bopkg9agc7394hebg" -ForegroundColor White
Write-Host "2. Click 'Environment' tab in left sidebar" -ForegroundColor White
Write-Host "3. Find 'DATABASE_URL' variable" -ForegroundColor White
Write-Host "4. Click 'Edit' button" -ForegroundColor White
Write-Host "5. Paste the URL (already in clipboard!)" -ForegroundColor Green
Write-Host "6. Click 'Save Changes'" -ForegroundColor White
Write-Host ""

# Copy to clipboard
$DATABASE_URL | Set-Clipboard

Write-Host "✅ DATABASE_URL copied to clipboard!" -ForegroundColor Green
Write-Host ""
Write-Host "Your DATABASE_URL:" -ForegroundColor Cyan
Write-Host "$DATABASE_URL" -ForegroundColor DarkGray
Write-Host ""

# Step 3: Open dashboard
Write-Host "`n🌐 Opening Render Dashboard..." -ForegroundColor Green
Start-Process "https://dashboard.render.com/web/srv-d72bopkg9agc7394hebg"

Write-Host "`n===================================================" -ForegroundColor Cyan
Write-Host "  NEXT STEPS" -ForegroundColor Yellow
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. ✅ DATABASE_URL is in your clipboard" -ForegroundColor Green
Write-Host "2. 🌐 Dashboard opened in browser" -ForegroundColor Green
Write-Host "3. 📝 Follow the steps above to add it" -ForegroundColor Yellow
Write-Host "4. 💾 Click 'Save Changes'" -ForegroundColor Yellow
Write-Host "5. ⏱️  Wait 5-10 minutes for redeploy" -ForegroundColor Yellow
Write-Host "6. 🎉 Your site will be LIVE!" -ForegroundColor Green
Write-Host ""

Read-Host "Press ENTER to close"
