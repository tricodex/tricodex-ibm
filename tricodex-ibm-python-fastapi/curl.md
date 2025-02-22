# ProcessLens API Documentation

## Base URL
```
http://localhost:8000
```

## Health Check
```bash
# Check API health
curl -X GET http://localhost:8000/health
```

## Process Analysis

### Start Analysis
```bash
# Analyze a process dataset (CSV)
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: multipart/form-data" \
  -F "file=@./datasets/customer_support_tickets.csv" \
  -F "project_name=Customer Support Analysis"
```

Response:
```json
{
  "message": "Analysis started",
  "task_id": "507f1f77bcf86cd799439011",
  "project": {
    "name": "Customer Support Analysis",
    "created_at": "2024-02-21T10:30:00Z",
    "file_type": "text/csv",
    "columns": ["timestamp", "customer_id", "agent", "status", ...],
    "row_count": 1000
  }
}
```

### Check Analysis Status
```bash
# Get analysis status and results
curl -X GET http://localhost:8000/status/507f1f77bcf86cd799439011
```

Response:
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "status": "completed",
  "progress": 100,
  "thoughts": [
    {
      "timestamp": "2024-02-21T10:30:05Z",
      "stage": "structure_analysis",
      "thought": "Dataset Structure 📊: Identified 5 key process entities with customer journey flow, average 12 touchpoints per case.",
      "progress": 20
    },
    {
      "timestamp": "2024-02-21T10:30:15Z",
      "stage": "pattern_mining",
      "thought": "Process Pattern 🔄: Most frequent pattern is escalation (35% of cases) with 2.5x longer resolution time.",
      "progress": 40
    }
    // ... more thoughts
  ],
  "results": {
    "structure": { ... },
    "patterns": [ ... ],
    "performance": { ... },
    "improvements": [ ... ],
    "synthesis": { ... }
  }
}
```

### List Projects
```bash
# Get list of analysis projects
curl -X GET "http://localhost:8000/projects?skip=0&limit=10"
```

## Specialized Analysis Endpoints

### Timing Analysis
```bash
# Analyze timing metrics
curl -X POST http://localhost:8000/analyze/timing \
  -H "Content-Type: multipart/form-data" \
  -F "file=@./datasets/customer_support_tickets.csv"
```

### Quality Analysis
```bash
# Analyze quality metrics
curl -X POST http://localhost:8000/analyze/quality \
  -H "Content-Type: multipart/form-data" \
  -F "file=@./datasets/customer_support_tickets.csv"
```

### Resource Analysis
```bash
# Analyze resource utilization
curl -X POST http://localhost:8000/analyze/resources \
  -H "Content-Type: multipart/form-data" \
  -F "file=@./datasets/customer_support_tickets.csv"
```

## Admin Operations

### Cleanup Old Data
```bash
# Clean up analyses older than 30 days
curl -X POST http://localhost:8000/admin/cleanup?days=30
```

## Postman Collection

You can import this curl collection into Postman using the following steps:

1. Create a new collection named "ProcessLens API"
2. Create environment variables:
   - `BASE_URL`: http://localhost:8000
   - `TASK_ID`: (to be filled after starting analysis)

3. Import the following requests:
   - Health Check (GET)
   - Start Analysis (POST)
   - Check Status (GET)
   - List Projects (GET)
   - Timing Analysis (POST)
   - Quality Analysis (POST)
   - Resource Analysis (POST)
   - Cleanup (POST)

4. Add tests for each request to verify response format and status codes.

### Example Postman Test Script
```javascript
// Test for Start Analysis response
pm.test("Analysis started successfully", function () {
    pm.response.to.have.status(202);
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('task_id');
    pm.environment.set("TASK_ID", jsonData.task_id);
});

// Test for Check Status response
pm.test("Status check returns valid data", function () {
    pm.response.to.have.status(200);
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('status');
    pm.expect(jsonData.thoughts).to.be.an('array');
});
```

## Error Responses

The API returns standard HTTP status codes and JSON error responses:

```json
{
  "error": "Error message description",
  "status_code": 400
}
```

Common status codes:
- 202: Accepted (Analysis started)
- 400: Bad Request
- 404: Not Found
- 413: Payload Too Large
- 500: Internal Server Error
- 503: Service Unavailable