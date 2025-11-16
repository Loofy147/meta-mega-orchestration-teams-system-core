# Artifact Contract: Data Team (DT-001) to Code Team (CT-002)

This document defines the formal contract for the data artifact produced by the Data Team (DT-001) and consumed by the Code Team (CT-002).

## 1. Artifact Format

The artifact **MUST** be a single JSON file named `resource_analysis.json`.

## 2. JSON Schema

The JSON object **MUST** adhere to the following structure:

| Key | Type | Description | Example Value |
| :--- | :--- | :--- | :--- |
| `timestamp` | String | ISO 8601 timestamp of when the data was collected. | `"2025-11-15T10:30:00Z"` |
| `team_id` | String | Identifier for the producing team. | `"Data Team"` |
| `resource_type` | String | The type of resource being reported. | `"Disk Usage"` |
| `metrics` | Object | A collection of key-value pairs for the resource metrics. | |
| `metrics.filesystem` | String | The filesystem being monitored. | `"/dev/root"` |
| `metrics.size_gb` | Float | Total size of the filesystem in Gigabytes. | `40.0` |
| `metrics.used_gb` | Float | Used space in Gigabytes. | `8.2` |
| `metrics.available_gb` | Float | Available space in Gigabytes. | `31.8` |
| `metrics.usage_percent` | Integer | Percentage of disk space used. | `21` |

**Example JSON Output:**

\`\`\`json
{
  "timestamp": "2025-11-15T10:30:00Z",
  "team_id": "Data Team",
  "resource_type": "Disk Usage",
  "metrics": {
    "filesystem": "/dev/root",
    "size_gb": 40.0,
    "used_gb": 8.2,
    "available_gb": 31.8,
    "usage_percent": 21
  }
}
\`\`\`
