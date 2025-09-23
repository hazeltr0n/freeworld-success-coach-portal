# Streamlit Deprecation Notes

## ⚠️ CRITICAL: `use_container_width` Parameter Deprecated

**Removal Date**: 2025-12-31
**Status**: Being removed from codebase

### What was removed:
```python
# OLD (deprecated)
st.dataframe(df, use_container_width=True)
st.plotly_chart(fig, use_container_width=True)

# NEW (correct)
st.dataframe(df)
st.plotly_chart(fig)
```

### Why:
Streamlit deprecated `use_container_width` and will remove it after 2025-12-31. The new default behavior is container-width by default.

### Files cleaned:
- app.py
- admin_market_dashboard.py
- companies_dashboard.py
- free_agents_dashboard.py
- app_utils.py

### 🔴 REMINDER FOR CLAUDE:
**STOP re-introducing `use_container_width` in new code!** It's deprecated and will break after 2025-12-31.