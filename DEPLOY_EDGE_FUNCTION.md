# Deploy Enhanced Feedback Edge Function

The enhanced feedback system edge function is ready to deploy but requires manual deployment due to access token requirements.

## Option 1: Manual Deployment via Supabase Dashboard

1. **Go to Supabase Dashboard**
   - Navigate to: https://supabase.com/dashboard
   - Select your project

2. **Go to Edge Functions**
   - Functions → Edge Functions

3. **Update job-feedback function**
   - Find the existing `job-feedback` function
   - Click "Edit" or create new if doesn't exist

4. **Copy Function Code**
   - Copy the entire contents of: `supabase/functions/job-feedback/index.ts`
   - Paste into the Supabase dashboard editor
   - Click "Deploy"

## Option 2: CLI Deployment (if you have access token)

```bash
# Set your Supabase access token
export SUPABASE_ACCESS_TOKEN="your_access_token_here"

# Deploy the function
supabase functions deploy job-feedback --no-verify-jwt
```

## What the Enhanced Function Does

- **Permanent Negative Feedback**: `requires_experience`, `not_fair_chance_friendly`
  → Sets `job_flagged = true` (permanent filter)

- **Temporary Negative Feedback**: `job_expired`
  → Increments `feedback_expired_links` counter + sets timestamp (72h expiry)

- **Positive Feedback**: `i_like_this_job`, `i_applied_to_this_job`
  → Increments `feedback_likes` counter

- **Application Tracking**: `i_applied_to_this_job`
  → Also increments agent's `total_applications` counter in `agent_profiles`

## Testing

After deployment, test with a feedback submission to verify:
1. Counters are properly incremented
2. Timestamps are set correctly
3. No errors in function logs

## Function URL

The function will be available at:
`https://[your-project-id].functions.supabase.co/job-feedback`