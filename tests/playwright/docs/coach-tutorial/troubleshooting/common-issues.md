# Common Issues & Solutions

## Search Issues

### "No results found" or Very Few Results

**Possible Causes & Solutions**:

1. **Location not recently searched**
   - Try **Indeed Fresh Only** instead of Memory Only
   - Check spelling of city and state
   - Try nearby major cities (Houston instead of smaller suburbs)

2. **Search terms too specific**
   - Use broader terms: "driver" instead of "CDL Class A experienced driver"
   - Try "CDL driver" instead of specific job titles
   - Remove extra qualifiers and requirements

3. **Small job market**
   - Increase job quantity from 25 to 100
   - Expand to nearby metro areas
   - Try different search terms relevant to the area

4. **Memory cache is stale**
   - Use Indeed Fresh to populate memory with current jobs
   - Wait a few hours and try Memory Only again
   - Check if other coaches have searched this location recently

### Search Takes Too Long or Times Out

**Solutions**:

1. **Reduce job quantity**
   - Use 25 jobs for testing, 100 for normal searches
   - Avoid 500+ unless necessary for comprehensive analysis

2. **Check search mode**
   - Memory Only should complete in 5 seconds
   - Indeed Fresh typically takes 30-90 seconds
   - If Memory Only is slow, refresh the page

3. **Network issues**
   - Check internet connection stability
   - Try again during off-peak hours
   - Close other bandwidth-intensive applications

4. **System load**
   - Try again in a few minutes
   - Use smaller job quantities during busy periods
   - Consider scheduling batch searches for off-hours

### Poor Quality Results (Too Many "Bad" Jobs)

**Improvements**:

1. **Refine search terms**
   - Use more specific, professional job titles
   - Add quality indicators: "CDL driver benefits"
   - Avoid terms that attract low-quality postings

2. **Try different classifier**
   - CDL Traditional for driving jobs
   - Career Pathways for warehouse/entry-level positions

3. **Location considerations**
   - Some markets have better job quality than others
   - Major metro areas often have higher-quality positions
   - Consider expanding search radius

## Interface Issues

### Can't Access Certain Tabs or Features

**Check Permissions**:
- **🗓️ Batches & Scheduling**: Requires `can_access_batches` permission
- **Google Jobs features**: Requires `can_access_google_jobs` permission
- **⚙️ Admin Panel**: Admin-only access
- **Advanced Analytics**: May require elevated permissions

**Solutions**:
1. Contact your administrator to verify permission levels
2. Log out and log back in to refresh permissions
3. Verify you're using the correct login credentials

### Page Not Loading or Stuck

**Troubleshooting Steps**:
1. **Refresh the page** (F5 or Ctrl+R)
2. **Clear browser cache** and try again
3. **Try different browser** (Chrome, Firefox, Edge)
4. **Check browser console** for error messages (F12 → Console tab)
5. **Disable browser extensions** that might interfere

### Login Issues

**Username/Password Not Working**:
1. Verify credentials are correct (check caps lock)
2. Try typing instead of copy/paste
3. Contact administrator if credentials should work
4. Check for account lockouts or expiration

**Login Form Not Appearing**:
1. Wait 15-30 seconds for page to fully load
2. Refresh the page if form doesn't appear
3. Try opening in incognito/private browsing mode
4. Clear browser cookies and cache

## Export and PDF Issues

### PDF Generation Fails

**Common Fixes**:
1. **Reduce job count** in PDF export settings
2. **Check browser popup blocker** - may block PDF download
3. **Try different browser** - some handle PDFs better
4. **Ensure search has results** before attempting export

### PDF Missing Jobs or Data

**Settings to Check**:
1. **Maximum jobs setting** - may be set too low
2. **Quality level filters** - ensure "Good" and "So-So" are selected
3. **Route type filters** - check both "Local" and "OTR" if needed
4. **Search completed fully** before export

## Performance Issues

### Slow Response Times

**Optimization Tips**:
1. **Use Memory Only** searches whenever possible
2. **Start with small job quantities** (25-100)
3. **Close unnecessary browser tabs** and applications
4. **Check internet speed** - may need better connection
5. **Search during off-peak hours** (early morning, late evening)

### High API Costs

**Cost Management**:
1. **Prioritize Memory Only** searches (free)
2. **Use Fresh searches strategically** only when needed
3. **Start with test quantities** (25 jobs) for new locations
4. **Set up batch schedules** to keep memory fresh automatically
5. **Coordinate with other coaches** to avoid duplicate fresh searches

## Getting Help

### When to Contact Support

- **Permission issues** you can't resolve
- **Persistent technical problems** after trying troubleshooting
- **System errors** or unusual behavior
- **Questions about best practices** for your specific use case

### Information to Include

1. **Exact error messages** (screenshot if possible)
2. **Steps you were taking** when issue occurred
3. **Browser and version** you're using
4. **Search parameters** you were trying to use
5. **Whether issue is consistent** or intermittent

### Self-Help Resources

- **[Field Definitions](../reference/field-definitions.md)** - Parameter explanations
- **[Daily Workflows](../daily-workflows/)** - Step-by-step guides
- **[Features Guide](../features-guide/)** - Detailed feature explanations

---
*For additional support, contact your system administrator*
