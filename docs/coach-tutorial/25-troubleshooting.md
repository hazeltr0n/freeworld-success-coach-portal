# Troubleshooting Common Issues

This guide covers the most common issues you might encounter as a coach and provides step-by-step solutions.

## 🔐 Login and Access Issues

### "Invalid username or password" Error
**Symptoms**: Cannot log into the platform
**Solutions**:
1. **Double-check credentials** - Ensure caps lock is off
2. **Try password reset** - Contact your administrator
3. **Clear browser cache** - Delete cookies and cached data
4. **Try incognito/private mode** - Rules out browser extension conflicts

### Platform Loads Slowly or Appears Broken
**Symptoms**: Pages don't load properly, missing elements
**Solutions**:
1. **Refresh the page** - Press Ctrl+F5 (or Cmd+Shift+R on Mac)
2. **Clear browser cache and cookies**
3. **Try a different browser** - Chrome, Firefox, Safari, Edge
4. **Check internet connection** - Ensure stable connectivity
5. **Disable browser extensions** - Ad blockers can interfere with functionality

### "Session expired" Messages
**Symptoms**: Suddenly logged out during work
**Solutions**:
1. **Log back in** - Sessions expire after inactivity
2. **Keep platform active** - Click around periodically during long sessions
3. **Save work frequently** - Don't rely on session persistence for unsaved data

## 🔍 Search Issues

### "No jobs found" Results
**Symptoms**: Search returns zero or very few jobs
**Troubleshooting Steps**:
1. **Check search parameters**:
   - Is the location spelled correctly?
   - Are search terms too specific? Try "CDL Driver" instead of "CDL Class A Local Driver"
   - Is the radius too small? Try 50+ miles for rural areas

2. **Try different markets**:
   - Some areas have limited CDL opportunities
   - Test with known high-volume markets (Houston, Atlanta, Phoenix)

3. **Use Memory vs Fresh mode**:
   - Fresh: Forces new API calls, may find recent postings
   - Memory: Uses cached results, faster but potentially older data

### Search Takes Too Long or Times Out
**Symptoms**: Search spins indefinitely or shows timeout error
**Solutions**:
1. **Reduce job limit**: Try 250 jobs instead of 1000
2. **Use fewer markets**: Limit to 2-3 markets instead of 5+
3. **Check API status**: Some sources may be temporarily unavailable
4. **Try exact location mode**: Enable "Use exact location only" checkbox
5. **Switch to Memory mode**: If you searched this area recently

### Poor Job Quality (Too Many "Bad" Jobs)
**Symptoms**: Most results are rated "Bad" by AI, few "Good" jobs
**Analysis Steps**:
1. **Check market characteristics**:
   - Rural areas may have more owner-operator postings
   - Some regions have more training/school positions

2. **Adjust search terms**:
   - Add "Company Driver" to exclude owner-operator
   - Include "Benefits" to find better positions
   - Try "No Experience CDL" for entry-level focus

3. **Review business rules**:
   - System automatically filters owner-operator and school bus
   - Low salary jobs may be filtered out

## 📊 Output Generation Problems

### PDF Generation Fails
**Symptoms**: Error message when creating PDF or blank PDF
**Solutions**:
1. **Ensure you have results**: Can't create PDF with zero jobs
2. **Check job limit**: Very large job lists (1000+) may cause issues
3. **Try smaller batches**: Generate PDF with top 100 jobs first
4. **Refresh and retry**: Temporary server issues can cause failures

### CSV Export Issues
**Symptoms**: CSV download fails or contains garbled data
**Solutions**:
1. **Use "Save As" instead of direct open**: Right-click download link
2. **Check browser download settings**: Ensure downloads aren't blocked
3. **Try different browser**: Some browsers handle CSV differently
4. **Open with correct application**: Use Excel, Google Sheets, or text editor

### Link Tracking Not Working
**Symptoms**: Short.io links not generating or not tracking clicks
**Troubleshooting**:
1. **Check internet connectivity**: Link generation requires API access
2. **Verify with test click**: Click your own generated link to test tracking
3. **Wait for analytics update**: Click tracking may take a few minutes to appear
4. **Check link sharing**: Ensure agents are clicking the tracked links, not original URLs

## 🤖 AI Classification Issues

### AI Gives Unexpected Job Ratings
**Symptoms**: Jobs you think are good rated as "so-so" or "bad"
**Understanding the AI**:
1. **AI focuses on Free Agent value**:
   - Competitive pay relative to market
   - Clear job requirements and benefits
   - Legitimate company with good reputation
   - Reasonable experience requirements

2. **Common reasons for "bad" ratings**:
   - Owner-operator positions (require truck ownership)
   - School bus driving (different license requirements)
   - Training positions with very low pay
   - Vague job descriptions
   - Companies with poor online reputation

3. **If ratings seem consistently wrong**:
   - Review job descriptions for missed context
   - Check if search terms are pulling irrelevant jobs
   - Consider market-specific factors (rural vs urban expectations)

### Classification Taking Too Long
**Symptoms**: AI classification step hangs or times out
**Solutions**:
1. **Reduce batch size**: Search for fewer jobs (250 vs 1000)
2. **Check OpenAI API status**: AI provider may have service issues
3. **Use Memory mode**: Reuse previous classifications when possible
4. **Force Fresh Classification**: Admin feature to bypass cache if needed

## 📱 Mobile and Browser Compatibility

### Platform Doesn't Work on Mobile
**Issue**: Interface broken or unusable on phone/tablet
**Recommendation**:
- **Use desktop/laptop**: Platform optimized for larger screens
- **Tablet in landscape**: May work for basic functions
- **Mobile browser in desktop mode**: Some mobile browsers offer this option

### Browser-Specific Issues
**Chrome**: Generally most reliable
**Firefox**: Good compatibility, may need pop-up blocker adjustments
**Safari**: Works well on Mac, may have cookie issues
**Edge**: Generally compatible, clear cache if issues occur
**Internet Explorer**: Not supported, please upgrade to modern browser

## 📊 Analytics and Performance Issues

### Analytics Not Updating
**Symptoms**: Click counts not changing, outdated metrics
**Solutions**:
1. **Wait for refresh cycle**: Analytics update every 15-30 minutes
2. **Check date filters**: May be looking at wrong time period
3. **Verify Free Agents clicking tracked links**: Not original job URLs
4. **Clear browser cache**: Force reload of analytics data

### Slow Performance During Peak Hours
**Symptoms**: Platform sluggish, searches take longer
**Understanding**:
- **Peak usage times**: Weekday mornings (8-11 AM) typically busiest
- **API rate limits**: Job search APIs may be slower during peak times
- **Solutions**:
  - Schedule intensive searches for off-peak hours
  - Use Memory mode when possible
  - Break large searches into smaller chunks

## 🔧 Advanced Troubleshooting

### JavaScript Errors in Browser Console
**For Technical Users**:
1. **Open browser dev tools** (F12)
2. **Check Console tab** for error messages
3. **Note specific error details** for technical support
4. **Screenshot errors** when reporting issues

### Network Connectivity Issues
**Symptoms**: Intermittent failures, partial page loads
**Diagnostics**:
1. **Test other websites**: Confirm general internet connectivity
2. **Check corporate firewall**: May block certain API endpoints
3. **Try VPN or hotspot**: Rule out network restrictions
4. **Contact IT department**: Corporate networks may need whitelist updates

### Data Inconsistencies
**Symptoms**: Job counts don't match, missing data in exports
**Investigation Steps**:
1. **Note specific search parameters** when issue occurred
2. **Try reproducing** with same search settings
3. **Compare different output formats** (PDF vs CSV)
4. **Document discrepancies** for technical support

## 📞 When to Contact Support

### Escalation Criteria
Contact your administrator or technical support when:
- **Security concerns**: Suspicious login attempts, account access issues
- **Data integrity problems**: Consistent wrong job counts, missing data
- **System-wide issues**: Platform completely unavailable
- **Billing/API concerns**: Unexpected costs or usage spikes
- **New coach setup**: Account creation, permission adjustments

### Information to Provide
When contacting support, include:
1. **Your coach username**
2. **Browser and version** (Chrome 91, Firefox 89, etc.)
3. **Operating system** (Windows 10, macOS, etc.)
4. **Specific error messages** (screenshot if possible)
5. **Steps to reproduce** the issue
6. **Time when issue occurred**
7. **Search parameters** if search-related

## ✅ Prevention Best Practices

### Daily Maintenance
- **Clear browser cache** weekly
- **Log out properly** at end of sessions
- **Keep browser updated** to latest version
- **Monitor your usage patterns** to avoid hitting limits

### Search Strategy
- **Start with smaller searches** (250 jobs) before scaling up
- **Test new markets** with sample searches first
- **Use Memory mode** for repeated searches in same day
- **Monitor API costs** and adjust search frequency accordingly

### Free Agent Communication
- **Test tracking links** before sharing with agents
- **Keep copies of shared job lists** for reference
- **Note agent preferences** to improve future search targeting
- **Follow up on engagement** to ensure links are working

---

**Remember**: Most issues are temporary and can be resolved with basic troubleshooting. When in doubt, try the simplest solution first (refresh, clear cache, try different browser) before escalating to technical support.

**Next**: Ready to optimize your approach? Check out [Best Practices](26-best-practices.md)

**Back to**: [Main Tutorial](README.md)