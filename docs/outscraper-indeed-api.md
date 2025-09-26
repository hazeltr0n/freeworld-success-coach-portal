# Outscraper Indeed API Documentation

**Time Completed**: Jul 24, 2025 6:28 AM PDT
**Source**: Official Outscraper API Documentation

## API Endpoint

```
GET https://api.outscraper.cloud/indeed-search
```

## Authentication

**Type**: ApiKeyAuth
**Header**: `X-API-KEY: your-api-key`

## Parameters

### `query` (required)
- **Type**: Array of strings
- **Description**: Search links with search parameters (e.g., `https://www.indeed.com/jobs?q=&l=Fremont+Canyon%2C+CA`)
- **Batching**: Supports up to **250 queries** in a single request
- **Format**: `query=text1&query=text2&query=text3`
- **Purpose**: Allows multiple queries to be sent in one request and save on network latency time

### `limit`
- **Type**: integer
- **Default**: 100
- **Description**: **The parameter specifies the limit of items to get from ONE query**
- **Important**: Each query in the array gets the full limit, not distributed

### `enrichment`
- **Type**: Array of strings
- **Available Options**:
  - `domains_service` - Emails & Contacts Scraper
  - `emails_validator_service` - Email Address Verifier
  - `company_websites_finder` - Company Website Finder
  - `disposable_email_checker` - Disposable Emails Checker
  - `company_insights_service` - Company Insights
  - `phones_enricher_service` - Phone Numbers Enricher
  - `trustpilot_service` - Trustpilot Scraper
  - `whitepages_phones` - Phone Identity Finder
  - `ai_chain_info` - Chain Info
- **Note**: Using enrichments increases response time; consider using `async=true`

### `fields`
- **Type**: string
- **Description**: Defines which fields to include in response
- **Default**: Returns all fields
- **Example**: `&fields=query,name` for specific fields only

### `async`
- **Type**: boolean
- **Default**: "true"
- **Options**:
  - `false`: Keep HTTP connection open until results ready
  - `true`: Submit request and retrieve later (1-3 minutes) via Request Results endpoint
- **Note**: Each response available for 2 hours after completion

### `ui`
- **Type**: boolean
- **Default**: "false"
- **Description**: Execute as UI task (platform task via API)
- **Effect**: Overwrites `async` parameter to `true`

### `webhook`
- **Type**: string
- **Description**: URL for POST callback when task/request finishes
- **Effect**: Overwrites webhook from integrations

## Response Codes

- **200**: Success - contains status and data array
- **202**: Async - contains request ID for later retrieval
- **204**: Request finished with failure, no results
- **401**: Wrong or missing API Key
- **402**: Past due invoices or payment method issues
- **422**: Wrong query URL parameters

## Response Format

```json
{
  "id": "your-request-id",
  "status": "Success",
  "data": [
    [] // Array where each element represents response for single query
  ]
}
```

## Key Implementation Points

### Multiple Query Behavior

**Example**: 3 search terms with limit=1000

```python
params = {
    'query': [
        'https://indeed.com/jobs?q=cdl+driver&l=Houston,TX',
        'https://indeed.com/jobs?q=class+a+driver&l=Houston,TX',
        'https://indeed.com/jobs?q=class+b+driver&l=Houston,TX'
    ],
    'limit': 1000,  # Each query gets 1000 jobs
    'async': 'false'
}
```

**Result**: Up to 3000 total jobs (1000 per query)

### Response Processing

```python
# API returns data[0], data[1], data[2] for each query
for i, query_result in enumerate(data['data']):
    if isinstance(query_result, list):
        all_jobs.extend(query_result)
        print(f"Query {i+1}: {len(query_result)} jobs")
```

### Current Implementation Status

✅ **CORRECT**: Our implementation multiplies limit by number of queries
✅ **CORRECT**: Each search term gets separate Indeed URL
✅ **CORRECT**: Single API call with array of queries
✅ **CORRECT**: Response processing flattens results from all queries

## Best Practices

1. **Async Processing**: Use `async=true` for large requests to avoid timeouts
2. **Batch Queries**: Up to 250 queries per request for efficiency
3. **Error Handling**: Check response status and handle 2xx codes appropriately
4. **Rate Limiting**: Respect API quotas and request limits
5. **Webhook Integration**: Use webhooks for async job completion notifications

## Batching Benefits

- **Network Efficiency**: Single request for multiple searches
- **Cost Optimization**: Reduced API call overhead
- **Time Savings**: Parallel processing of multiple queries
- **Simplified Management**: One request ID for multiple searches

---

**Documentation Source**: Outscraper Official API Documentation
**Last Updated**: July 24, 2025