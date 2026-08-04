# feat: add admin-only job configuration API

## Overview

This PR adds backend support for the admin Job Configuration feature.

Administrators can retrieve and update job-level processing limits and AI model settings by Job ID. The configuration is stored in the existing `job` table and is protected by both Firebase authentication and backend administrator authorization.

The frontend implementation is submitted in a separate pull request.

## Task Requirements

The Job Configuration feature supports the following fields:

- Resume Process Limit
- Interview Limit
- Resume Process Model
- Interview Model

The backend is responsible for:

- Loading the configuration for a specified Job ID
- Returning basic job information together with configuration values
- Validating configuration updates
- Persisting changes to MySQL
- Rejecting unauthenticated requests
- Rejecting authenticated non-admin requests
- Returning appropriate HTTP status codes for invalid or non-existent jobs

## Implementation Details

### 1. Job Entity

The following fields were added to the existing `Job` entity:

- `resumeProcessLimit`
- `interviewLimit`
- `resumeProcessModel`
- `interviewModel`

Default values are defined for existing and newly created jobs:

```text
Resume Process Limit: 100
Interview Limit: 50
Resume Process Model: gpt-4o-mini
Interview Model: gpt-4o
```

### 2. Database Migration

A database migration script was added at:

```text
docs/db/r5_job_configuration.sql
```

The migration adds the following columns to the `job` table:

```sql
resume_process_limit INT NOT NULL DEFAULT 100
interview_limit INT NOT NULL DEFAULT 50
resume_process_model VARCHAR(100) NOT NULL DEFAULT 'gpt-4o-mini'
interview_model VARCHAR(100) NOT NULL DEFAULT 'gpt-4o'
```

The defaults allow existing jobs to continue working without requiring manual backfilling.

### 3. Request and Response Models

Added:

```text
JobConfigurationUpdateRequest
JobConfigurationResponse
```

`JobConfigurationUpdateRequest` represents the editable configuration submitted by the frontend.

`JobConfigurationResponse` returns both:

- Basic job information
- Job configuration values

Example response:

```json
{
  "job": {
    "id": "01f5c16e-e144-40b4-a231-87ec4e410c98",
    "title": "Software engineer test",
    "companyName": "Example Company",
    "status": "ACTIVE"
  },
  "configuration": {
    "resumeProcessLimit": 120,
    "interviewLimit": 60,
    "resumeProcessModel": "gpt-4o-mini",
    "interviewModel": "gpt-4o"
  }
}
```

### 4. Service Layer

Added service methods for:

- Retrieving job configuration by Job ID
- Updating job configuration
- Persisting changes through JPA
- Returning `404 Not Found` when the Job ID does not exist

The update operation validates that:

- Job ID is provided
- Resume Process Limit is a positive integer
- Interview Limit is a positive integer
- Resume Process Model is not blank
- Interview Model is not blank
- Model names do not exceed 100 characters

The job modification timestamp is updated when the configuration changes.

### 5. API Endpoints

#### Get Job Configuration

```http
GET /job/configuration?jobId={jobId}
```

Returns the job summary and current configuration.

#### Update Job Configuration

```http
POST /job/update/configuration
Content-Type: application/json
```

Example request:

```json
{
  "jobId": "01f5c16e-e144-40b4-a231-87ec4e410c98",
  "resumeProcessLimit": 120,
  "interviewLimit": 60,
  "resumeProcessModel": "gpt-4o-mini",
  "interviewModel": "gpt-4o"
}
```

### 6. Authentication and Authorization

Both endpoints use `@RequireAuth`, so the Firebase token is validated before the controller is executed.

After successful token verification, the authentication interceptor stores the verified Firebase email in the request attribute:

```text
firebaseEmail
```

The controller then:

1. Reads the authenticated Firebase email
2. Looks up the corresponding `HiringClient`
3. Verifies that the user has `HiringClient.Role.admin`
4. Returns `403 Forbidden` when the authenticated user is not an administrator

This authorization check is enforced by the backend and does not rely only on frontend route visibility or frontend role values.

## Request Flow

```text
Admin frontend
      ↓
Pinia API store
      ↓
Firebase Authorization token
      ↓
FirebaseAuthInterceptor
      ↓
JobController administrator authorization check
      ↓
JobService validation and update
      ↓
JobRepository / JPA
      ↓
MySQL job table
```

## Screenshots and Verification

### 1. Existing Job Configuration Loaded

An administrator can enter a Job ID and load the existing job information and configuration values.

<!-- Drag screenshot 1 here -->

This screenshot should demonstrate:

- Job ID-based lookup
- Job information returned by the backend
- Configuration values loaded from the database
- Successful authenticated administrator access

### 2. Job Configuration Updated Successfully

The administrator can update the resume and interview limits and save the new configuration.

<!-- Drag screenshot 2 here -->

This screenshot should demonstrate:

- Editable configuration fields
- Successful update request
- Successful response from the backend
- Updated configuration displayed by the frontend

### 3. Database Persistence Verification

The updated values remain in the database after the configuration is saved and loaded again.

<!-- Drag screenshot 3 here -->

Example verification:

```text
resume_process_limit = 120
interview_limit = 60
resume_process_model = gpt-4o-mini
interview_model = gpt-4o
```

This confirms that the feature is connected to MySQL and is not using temporary frontend state or mock data.

### 4. Successful Administrator Request — 200 OK

An authenticated administrator can access the configuration endpoint successfully.

<!-- Drag screenshot 4 here -->

Expected result:

```text
GET /job/configuration → 200 OK
POST /job/update/configuration → 200 OK
```

### 5. Missing Authentication — 401 Unauthorized

A direct API request without an Authorization token is rejected.

<!-- Drag screenshot 5 here -->

Expected result:

```text
401 Unauthorized
```

This confirms that the endpoint cannot be accessed without a valid Firebase token.

### 6. Authenticated Non-admin User — 403 Forbidden

An authenticated user without the administrator role is rejected even when directly calling the backend endpoint.

<!-- Drag screenshot 6 here -->

Expected result:

```text
403 Forbidden
```

This confirms that frontend route protection is not the only security boundary. The backend independently verifies the authenticated user's database role.

### 7. Non-existent Job ID — 404 Not Found

An authenticated administrator requesting a Job ID that does not exist receives a not-found response.

<!-- Drag screenshot 7 here -->

Expected result:

```text
404 Not Found
```

This confirms that missing resources are handled separately from authentication and authorization failures.

### 8. Invalid Configuration — 400 Bad Request

Invalid configuration values are rejected before persistence.

<!-- Drag screenshot 8 here -->

Example invalid request:

```json
{
  "resumeProcessLimit": 0,
  "interviewLimit": -1,
  "resumeProcessModel": "",
  "interviewModel": ""
}
```

Expected result:

```text
400 Bad Request
```

## Test Matrix

| Test case | Expected result | Verified |
|---|---:|:---:|
| Admin loads an existing job configuration | `200 OK` | ✅ |
| Admin updates a valid configuration | `200 OK` | ✅ |
| Updated values persist in MySQL | Values remain after reload | ✅ |
| Request without Firebase token | `401 Unauthorized` | ✅ |
| Authenticated non-admin request | `403 Forbidden` | ✅ |
| Admin requests a non-existent Job ID | `404 Not Found` | ✅ |
| Resume Process Limit is zero or negative | `400 Bad Request` | ✅ |
| Interview Limit is zero or negative | `400 Bad Request` | ✅ |
| Resume Process Model is blank | `400 Bad Request` | ✅ |
| Interview Model is blank | `400 Bad Request` | ✅ |

## Validation

The backend build was verified with:

```bash
./gradlew clean build -Plocal
```

Additional manual validation included:

- Loading configuration for an existing Job ID
- Updating numeric limit values
- Updating model configuration values
- Reloading the job after saving
- Verifying persisted values directly in MySQL
- Testing authenticated administrator access
- Testing requests without authentication
- Testing authenticated non-admin access
- Testing a non-existent Job ID
- Testing invalid configuration input

## Files Changed

```text
recruitdirect-domain/src/main/java/com/recruitdirect/model/entity/Job.java
recruitdirect-domain/src/main/java/com/recruitdirect/service/JobService.java
recruitdirect-service/src/main/java/com/recruitdirect/controller/JobController.java
recruitdirect-service/src/main/java/com/recruitdirect/model/JobConfigurationResponse.java
recruitdirect-service/src/main/java/com/recruitdirect/model/JobConfigurationUpdateRequest.java
docs/db/r5_job_configuration.sql
```

## Related Frontend PR

<!-- Add the frontend PR link here -->
