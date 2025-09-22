# 🧪 Manual Refresh Button Test Guide

## Quick Test Steps

### 1. Enable pg_cron (One-time setup)
In Supabase SQL Editor, run:
```sql
CREATE EXTENSION IF NOT EXISTS pg_cron;
```

### 2. Setup Functions (One-time)
Run the SQL from `setup_scheduled_analytics.sql` in Supabase SQL Editor.

### 3. Test Companies Manual Refresh
1. Go to your Streamlit app
2. Navigate to **Companies** tab
3. Look for **4 buttons** at the top:
   - 🔄 Update Companies Data
   - **⚡ Manual Refresh** ← NEW BUTTON
   - 🤝 Fair Chance Only (checkbox)
   - 🌍 Filter by Market (dropdown)
4. Click **⚡ Manual Refresh**
5. Should see: "Running manual companies refresh..." spinner
6. Should see: "✅ Manual refresh completed! Updated X companies."

### 4. Test Free Agents Manual Refresh
1. Navigate to **Free Agents** tab → **📊 Analytics** sub-tab
2. Look for **5 buttons** at the top:
   - 🔄 Update Analytics Data
   - **⚡ Manual Refresh** ← NEW BUTTON
   - 👨‍🏫 My Agents Only (checkbox)
   - 🎯 Activity Level (dropdown)
   - 🌍 Market Filter (dropdown)
3. Click **⚡ Manual Refresh**
4. Should see: "Running manual agents refresh..." spinner
5. Should see: "✅ Manual refresh completed! Updated X agents."

### 5. Verify Logging (Optional)
Check logs in Supabase SQL Editor:
```sql
SELECT * FROM analytics_rollup_log
ORDER BY executed_at DESC
LIMIT 5;
```

## ✅ What You Should See

### Companies Tab
- **Button Count**: 4 controls total (was 3, now 4)
- **New Button**: ⚡ Manual Refresh between "Update" and "Fair Chance Only"
- **Success Message**: Shows number of companies updated
- **Function Called**: `scheduled_companies_refresh()`

### Free Agents Analytics Tab
- **Button Count**: 5 controls total (was 4, now 5)
- **New Button**: ⚡ Manual Refresh between "Update" and "My Agents Only"
- **Success Message**: Shows number of agents updated
- **Function Called**: `scheduled_agents_refresh()`

## 🚫 Troubleshooting

| Error | Solution |
|-------|----------|
| "Supabase client not available" | Check environment variables in Streamlit |
| "Function does not exist" | Run `setup_scheduled_analytics.sql` |
| "Permission denied" | Enable `pg_cron` extension |
| No new button visible | Clear browser cache / hard refresh |

## 🎯 Testing Benefits

- **Blacklist Testing**: Update company blacklist → manual refresh → see immediate impact
- **Click Tracking**: Generate clicks → manual refresh → see analytics update
- **Engagement Scoring**: Agent activity → manual refresh → see engagement scores
- **Real-time Debugging**: No waiting for scheduled execution times

## 📊 Expected Results

Both manual refresh buttons should:
1. ✅ Execute Supabase database functions directly
2. ✅ Show spinner with descriptive text
3. ✅ Display success message with update count
4. ✅ Refresh the page to show updated data
5. ✅ Log execution details to `analytics_rollup_log` table

The manual refresh complements automated scheduling - you get both scheduled background updates AND on-demand testing capabilities!