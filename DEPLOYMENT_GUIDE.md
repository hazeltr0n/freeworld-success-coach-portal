# FreeWorld Background Job Scheduler - Deployment Guide

## 🚀 **Making "Save for Later" Actually Work**

This guide will help you deploy the background job scheduler that makes scheduled jobs actually run automatically.

## 📋 **Prerequisites**

1. **Database Migration**: Add the `scheduled_run_at` field
2. **Python Environment**: Same environment as the main app
3. **Always-On Server**: Process that never stops

## 🗄️ **Step 1: Database Migration**

Run this SQL in your Supabase dashboard or via CLI:

```sql
-- Add scheduled_run_at field to async_job_queue table
ALTER TABLE async_job_queue
ADD COLUMN scheduled_run_at TIMESTAMPTZ NULL;

-- Add index for efficient querying
CREATE INDEX idx_async_job_queue_scheduled_ready
ON async_job_queue (status, scheduled_run_at)
WHERE status = 'scheduled' AND scheduled_run_at IS NOT NULL;
```

## 🐍 **Step 2: Test the Scheduler Locally**

```bash
# Test that all dependencies work
python background_job_scheduler.py

# Should output:
# 🚀 FreeWorld Background Job Scheduler
# =====================================
# This process will run continuously to execute scheduled jobs.
# Press Ctrl+C to stop.
```

## 🖥️ **Step 3: Production Deployment Options**

### **Option A: Simple Background Process (Recommended for testing)**

```bash
# Run in background with nohup
nohup python background_job_scheduler.py > scheduler.log 2>&1 &

# Check it's running
ps aux | grep background_job_scheduler

# Monitor logs
tail -f scheduler.log
```

### **Option B: Systemd Service (Recommended for production)**

Create `/etc/systemd/system/freeworld-scheduler.service`:

```ini
[Unit]
Description=FreeWorld Background Job Scheduler
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/freeworld-job-scraper-qa
ExecStart=/usr/bin/python3 background_job_scheduler.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=/path/to/freeworld-job-scraper-qa

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable freeworld-scheduler
sudo systemctl start freeworld-scheduler
sudo systemctl status freeworld-scheduler
```

### **Option C: Docker Container**

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "background_job_scheduler.py"]
```

### **Option D: Cloud Function (Advanced)**

For true serverless, you'd need to modify the scheduler to run as a triggered function rather than a continuous loop.

## 📊 **Step 4: Monitoring & Maintenance**

### **Check Scheduler Status**
```bash
# Check if process is running
ps aux | grep background_job_scheduler

# Check logs
tail -f background_scheduler.log

# Check recent scheduled jobs in database
```

### **Log File Locations**
- `background_scheduler.log` - Main scheduler logs
- Logs show: job processing, errors, timing info

### **Key Metrics to Monitor**
- Scheduler uptime
- Jobs processed per day
- Error rates
- Database connection health

## 🧪 **Step 5: Testing End-to-End**

1. **Create a Test Schedule**:
   - Use "Save for Later" in the app
   - Set schedule for 2 minutes from now
   - Check Scheduled Batches table

2. **Verify Background Processing**:
   - Wait for scheduled time
   - Check logs: `tail -f background_scheduler.log`
   - Verify job status changes from `scheduled` → `processing` → `completed`

3. **Check Results**:
   - Results appear in Supabase
   - Coach gets notification
   - Jobs show in completed jobs table

## 🚨 **Troubleshooting**

### **Scheduler Won't Start**
- Check Python path and dependencies
- Verify Supabase connection
- Check file permissions

### **Jobs Not Processing**
- Check database `scheduled_run_at` field exists
- Verify jobs have `status = 'scheduled'`
- Check scheduler logs for errors

### **Performance Issues**
- Monitor database query performance
- Check API rate limits (Indeed, Google, OpenAI)
- Monitor memory usage

## 🎯 **Success Criteria**

When working properly:
- ✅ "Save for Later" creates jobs with `status = 'scheduled'`
- ✅ Background scheduler runs continuously
- ✅ Jobs execute at scheduled times automatically
- ✅ Coaches receive notifications when jobs complete
- ✅ Results appear in job boards and analytics

## 🔄 **The Complete Flow**

```
User clicks "Save for Later"
    ↓
Job created with status='scheduled'
    ↓
Background scheduler detects ready job
    ↓
Executes job (Indeed sync or Google async)
    ↓
Updates job status to 'completed'
    ↓
Coach gets notification
    ↓
Results available in app
```

**Now "Save for Later" actually means "Save for Later" instead of "Run Right Now"!** 🎉