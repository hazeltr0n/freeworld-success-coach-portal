# 🧪 FreeWorld QA/Staging Portal

**This is your STAGING environment** - an exact copy of the main app where you can safely test changes before they go live.

## 🎯 Purpose

- **Test new features** before deploying to production
- **Debug issues** in a safe environment
- **Train new staff** without affecting live system
- **Experiment with configurations** without risk

## 🚀 How It Works

### Production vs Staging
```
Production Portal  →  Live coaches use daily  →  STABLE VERSION
QA/Staging Portal  →  Test changes here first  →  TESTING VERSION
```

### Workflow
1. **Make changes** in this QA portal
2. **Test thoroughly** - everything works the same as production
3. **Once satisfied**, copy the working changes to main production portal
4. **Deploy to production** knowing it's been tested

## 📋 Setup Instructions

### 1. Deploy QA Portal to Streamlit Cloud

1. **Create GitHub repo** for this QA portal:
   - Repository name: `freeworld-qa-portal`  
   - Public repository
   - Push this code to GitHub

2. **Deploy to Streamlit Cloud**:
   - New app → Select your QA repo
   - Branch: `main`
   - Main file: `app.py`
   - **Use SAME environment variables as production**
   - App name: `freeworld-qa-portal`

### 2. Environment Variables
Use the **exact same** environment variables as your production portal:

```bash
OPENAI_API_KEY=sk-your-key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-key
AIRTABLE_API_KEY=your-key
AIRTABLE_BASE_ID=your-base
AIRTABLE_TABLE_ID=your-table
SHORTIO_API_KEY=your-key
SHORTIO_DOMAIN=your-domain
```

## 🧪 Testing Features

### QA Banner
- Red banner at top clearly identifies this as TEST environment
- Prevents confusion with production portal
- Always visible to remind users this is staging

### Full Functionality
- **Exact same features** as production
- **Same database** (uses your real data for realistic testing)
- **Same user accounts** (coaches can log in normally)
- **Same integrations** (Airtable, Supabase, OpenAI, etc.)

### Safe Testing
- Changes here **don't affect production**
- Test job searches, agent management, analytics, etc.
- Experiment with new settings safely

## 🔄 Updating Process

### When You Want to Test Changes:
1. **Edit files** in this QA portal repository
2. **Git commit and push** changes
3. **QA Streamlit auto-deploys** the changes
4. **Test thoroughly** in the QA environment
5. **If working well**, copy changes to main production repo

### Example Workflow:
```bash
# Test a new feature in QA
cd freeworld-qa-portal
# Make your changes to files
git add .
git commit -m "Test: new job filtering feature"
git push

# QA portal auto-updates, test the feature
# If it works well, copy to production:

cd ../freeworld-job-scraper  
# Copy the working changes here
git add .
git commit -m "Add new job filtering feature (tested in QA)"
git push
# Production portal updates with tested feature
```

## ⚠️ Important Notes

### Same Database
- QA uses your **real production database**
- Changes to data (like adding agents) **will appear in production**
- This is intentional - gives you realistic testing with real data
- Be careful when testing data modifications

### Safe Testing
- **Code changes** are isolated (QA vs Production)
- **Data changes** are shared (same Supabase database)
- Test features like job searches, classifications, analytics
- Avoid testing bulk data operations that might affect production

### User Access
- Coaches can log into **both** portals with same credentials
- QA portal has red banner so they know it's testing
- Use QA for training new coaches safely

## 📈 Benefits

- ✅ **Risk-free testing** of new features
- ✅ **Realistic environment** with real data  
- ✅ **Easy comparison** between staging and production
- ✅ **Safe training environment** for new users
- ✅ **Debug complex issues** without affecting live system

## 🔗 Deployment URLs

Once deployed, you'll have:
- **Production**: `your-main-app.streamlit.app` (stable, coaches use daily)
- **QA/Staging**: `your-qa-app.streamlit.app` (testing, red banner)

**Perfect for testing changes before they go live! 🧪✨**