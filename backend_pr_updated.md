# feat: add admin job configuration and enforce per-job quotas

## Overview

This PR adds backend support for the admin Job Configuration feature.

Administrators can retrieve and update job-level processing limits and AI model settings by Job ID. The configuration is stored in the existing `job` table and is protected by both Firebase authentication and backend administrator authorization.

This PR also adds per-job quota enforcement for resume processing and interviews. The backend tracks actual usage, prevents new requests after the configured limit is reached, and sends a one-time warning email when usage reaches 80% of the configured quota.

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
- Returning current resume and interview usage
- Validating configuration updates
- Persisting changes to MySQL
- Enforcing resume processing limits
- Enforcing interview limits
- Tracking quota consumption
- Sending a one-time warning email when usage reaches 80% of the configured limit
- Preventing additional processing after quota exhaustion
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

The following quota tracking fields were also added:

- `resumeProcessUsed`
- `interviewUsed`
- `resumeProcessWarningSentAt`
- `interviewWarningSentAt`

Usage counters default to `0`, and warning timestamps default to `NULL`.

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

A second migration was added at:

```text
docs/db/r6_job_quota_usage.sql
```

It adds:

```sql
resume_process_used INT NOT NULL DEFAULT 0
interview_used INT NOT NULL DEFAULT 0
resume_process_warning_sent_at DATETIME NULL
interview_warning_sent_at DATETIME NULL
```

The defaults allow existing jobs to continue working without requiring manual backfilling.

### 3. Request and Response Models

Added:

```text
JobConfigurationUpdateRequest
JobConfigurationResponse
```

`JobConfigurationUpdateRequest` represents the editable configuration submitted by the frontend.

`JobConfigurationResponse` returns basic job information, configuration values, and current quota usage.

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
    "resumeProcessUsed": 0,
    "interviewLimit": 60,
    "interviewUsed": 0,
    "resumeProcessModel": "gpt-4o-mini",
    "interviewModel": "gpt-4o"
  }
}
```

Quota usage fields are read-only and are not accepted from the frontend update request.

### 4. Service Layer

Added service methods for:

- Retrieving job configuration by Job ID
- Updating job configuration
- Persisting changes through JPA
- Reserving resume quota
- Releasing resume quota
- Reserving interview quota
- Releasing interview quota
- Claiming warning notification state
- Clearing warning notification state when notification delivery fails
- Returning `404 Not Found` when the Job ID does not exist

The update operation validates that:

- Job ID is provided
- Resume Process Limit is a positive integer
- Interview Limit is a positive integer
- Resume Process Model is not blank
- Interview Model is not blank
- Model names do not exceed 100 characters

The job modification timestamp is updated when the configuration changes.

### 5. Quota Enforcement

Resume processing and interview initialization now reserve quota before continuing the workflow.

Quota reservation is performed atomically in the database using a conditional update so concurrent requests cannot exceed the configured limit.

Conceptually:

```sql
UPDATE job
SET interview_used = interview_used + 1
WHERE id = ?
  AND interview_used < interview_limit;
```

The same pattern is used for resume processing.

Quota behavior:

```text
used < limit
→ request is accepted
→ used increases by 1

used == limit
→ new request is rejected
→ used remains unchanged
```

For example, with a limit of 5:

```text
Request 1 → Used = 1
Request 2 → Used = 2
Request 3 → Used = 3
Request 4 → Used = 4
Request 5 → Used = 5
Request 6 → rejected, Used remains 5
```

### 6. 80% Warning Notification

A warning email is sent when usage reaches 80% of the configured limit.

The threshold is calculated as:

```text
ceil(limit × 0.8)
```

For example:

```text
Limit = 5
Warning threshold = 4
```

The warning timestamp prevents duplicate notifications.

If the warning email fails:

- The successfully consumed quota is retained
- The warning timestamp is cleared
- A later request can retry the warning notification

There is no separate 100% warning email. Once the quota is full, subsequent requests are blocked.

### 7. Resume Processing Quota

Resume processing consumes one quota unit when a new processing request is accepted.

If processing fails before successful creation, the reserved quota is released.

If the configured quota has already been reached, the request is rejected and usage does not increase.

### 8. Interview Quota

Interview initialization reserves one quota unit before creating the interview context.

If quota is exhausted, the backend returns:

```http
409 Conflict
```

with:

```json
{
  "error": "INTERVIEW_QUOTA_EXCEEDED",
  "message": "Interview limit reached for this job."
}
```

If interview creation fails before the context is successfully persisted, the reserved quota is released.

Candidate abandonment after successful interview initialization does not release the quota.

### 9. Warning Reset Behavior

If an administrator increases a configured limit and current usage falls below the new 80% threshold, the warning timestamp is reset. If usage remains at or above the new 80% threshold, the warning state is preserved.

### 10. Limit Updates Preserve Historical Usage

Changing a configured limit does not overwrite the actual usage count.

Example:

```text
Before:
Interview Limit = 5
Interview Used = 5

Admin changes limit to:
Interview Limit = 3

Result:
Interview Limit = 3
Interview Used = 5
```

### 11. API Endpoints

#### Get Job Configuration

```http
GET /job/configuration?jobId={jobId}
```

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

Usage counters are intentionally excluded from the update payload.

### 12. Authentication and Authorization

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

### Admin Configuration

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

### Resume Quota

```text
Resume upload request
      ↓
Reserve resume quota atomically
      ↓
Quota available?
   ↙           ↘
 Yes           No
  ↓             ↓
Process       Reject request
resume        without increment
```

### Interview Quota

```text
Interview initialization
      ↓
Reserve interview quota atomically
      ↓
Quota available?
   ↙           ↘
 Yes           No
  ↓             ↓
Create        409 Conflict
interview
context
```

## Screenshots and Verification

### 1. Existing Job Configuration Loaded

An administrator can enter a Job ID and load the existing job information and configuration values.

<img width="1507" height="822" alt="Pasted Graphic 1" src="https://github.com/user-attachments/assets/ccd57325-2cdf-42e2-9686-13a762825b81" />

### 2. Job Configuration Updated Successfully

The administrator can update the resume and interview limits and save the new configuration.

<img width="1207" height="763" alt="Pasted Graphic 2" src="https://github.com/user-attachments/assets/803ad556-2de5-4dc0-bfcc-6364e5161b9c" />

### 3. Database Persistence Verification

<img width="1232" height="730" alt="Admin Job Configuration" src="https://github.com/user-attachments/assets/491f8381-a1f7-45b6-b3e0-d7dd71f7bbc7" />

### 4. Successful Administrator Request — 200 OK

<img width="495" height="179" alt="Headers Payload" src="https://github.com/user-attachments/assets/9886718c-77fe-43ec-ba23-afa8bb94d22d" />

### 5. Missing Authentication — 401 Unauthorized

<img width="518" height="189" alt="Headers" src="https://github.com/user-attachments/assets/01cb42c6-db36-440f-883c-59f086c22c19" />

### 6. Authenticated Non-admin User — 403 Forbidden

<img width="776" height="200" alt="Response" src="https://github.com/user-attachments/assets/fb4be322-9fb1-44b2-bad7-6bae48dcc04d" />

### 7. Non-existent Job ID — 404 Not Found

<img width="1335" height="736" alt="Pasted Graphic 7" src="https://github.com/user-attachments/assets/b39b4c33-12cd-4d87-947e-c7af2649d21b" />

### 8. Interview Quota — 80% Warning

For a test job configured with:

```text
Interview Limit = 5
Interview Used = 4
```

the backend reached the 80% threshold, persisted the warning timestamp, and sent the warning email.

[ADD SCREENSHOT: DB showing `interview_limit = 5`, `interview_used = 4`, and warning timestamp]

[ADD SCREENSHOT: Interview quota warning email]

### 9. Interview Quota — Limit Enforcement

The fifth interview request was accepted. The next request returned:

```text
409 Conflict
```

The database remained:

```text
Interview Limit = 5
Interview Used = 5
```

[ADD SCREENSHOT: Interview request rejected with 409]

[ADD SCREENSHOT: DB still showing 5 / 5]

### 10. Resume Quota — 80% Warning

For a test job configured with:

```text
Resume Process Limit = 5
Resume Process Used = 3
```

one additional resume processing request increased usage to `4`, reaching the 80% threshold and triggering the warning email.

[ADD SCREENSHOT: DB showing `resume_process_limit = 5`, `resume_process_used = 4`, and warning timestamp]

[ADD SCREENSHOT: Resume quota warning email]

### 11. Resume Quota — Limit Enforcement

The fifth resume processing request was accepted. The next request was rejected.

The database remained:

```text
Resume Process Limit = 5
Resume Process Used = 5
```

[ADD SCREENSHOT: Rejected resume request]

[ADD SCREENSHOT: DB still showing 5 / 5]

### 12. Admin Usage Display

The Job Configuration response now includes current usage, and the frontend displays the values as read-only fields.

```text
Resume Process Limit: 5
Used: 5

Interview Limit: 5
Used: 5
```

[ADD SCREENSHOT: Admin Job Configuration showing quota usage]

### 13. Limit Update Preserves Usage

The interview limit was changed from `5` to `3` while historical usage remained `5`.

[ADD SCREENSHOT: Admin UI or DB showing limit 3 / used 5]

## Automated Tests

### InterviewServiceQuotaTest

Coverage includes:

- Successful quota reservation
- Quota exhausted
- Interview creation failure releases quota
- 80% warning claim
- Duplicate warning prevention
- Email failure clears the warning claim
- Email failure does not release successfully consumed quota

### JobServiceQuotaTest

Coverage includes:

- Successful resume quota reservation
- Resume quota rejected at limit
- Successful interview quota reservation
- Interview quota rejected at limit
- Resume warning reset when the new limit moves usage below 80%
- Interview warning reset when the new limit moves usage below 80%
- Warning state preserved when usage remains at or above 80%

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
| Interview quota below limit | Request accepted | ✅ |
| Interview reaches 80% usage | Warning sent once | ✅ |
| Interview reaches configured limit | Final allowed request succeeds | ✅ |
| Interview exceeds configured limit | `409 Conflict`, usage unchanged | ✅ |
| Resume quota below limit | Request accepted | ✅ |
| Resume reaches 80% usage | Warning sent once | ✅ |
| Resume reaches configured limit | Final allowed request succeeds | ✅ |
| Resume exceeds configured limit | Request rejected, usage unchanged | ✅ |
| Warning email fails | Usage retained, warning state cleared | ✅ |
| Admin lowers limit below current usage | Historical usage retained | ✅ |

## Validation

The backend build was verified with:

```bash
./gradlew clean build -Plocal
```

Quota-specific tests:

```bash
./gradlew :recruitdirect-domain:test \
--tests "com.recruitdirect.service.InterviewServiceQuotaTest" \
--tests "com.recruitdirect.service.JobServiceQuotaTest"
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
- Testing interview quota consumption
- Testing resume quota consumption
- Triggering the 80% interview warning
- Triggering the 80% resume warning
- Receiving real warning emails
- Filling interview quota to the configured limit
- Filling resume quota to the configured limit
- Confirming subsequent requests are rejected
- Confirming usage remains unchanged after quota exhaustion
- Confirming warning notifications are not duplicated
- Confirming admin limit changes do not overwrite historical usage

## Files Changed

```text
recruitdirect-domain/src/main/java/com/recruitdirect/model/entity/Job.java
recruitdirect-domain/src/main/java/com/recruitdirect/model/entity/InterviewContext.java
recruitdirect-domain/src/main/java/com/recruitdirect/repository/JobRepository.java
recruitdirect-domain/src/main/java/com/recruitdirect/service/EmailService.java
recruitdirect-domain/src/main/java/com/recruitdirect/service/InterviewService.java
recruitdirect-domain/src/main/java/com/recruitdirect/service/InterviewQuotaExceededException.java
recruitdirect-domain/src/main/java/com/recruitdirect/service/JobService.java

recruitdirect-service/src/main/java/com/recruitdirect/controller/JobController.java
recruitdirect-service/src/main/java/com/recruitdirect/controller/ResumeController.java
recruitdirect-service/src/main/java/com/recruitdirect/exception/GlobalExceptionHandler.java
recruitdirect-service/src/main/java/com/recruitdirect/model/JobConfigurationResponse.java
recruitdirect-service/src/main/java/com/recruitdirect/model/JobConfigurationUpdateRequest.java

recruitdirect-domain/src/test/java/com/recruitdirect/service/InterviewServiceQuotaTest.java
recruitdirect-domain/src/test/java/com/recruitdirect/service/JobServiceQuotaTest.java

docs/db/r5_job_configuration.sql
docs/db/r6_job_quota_usage.sql
```

## Follow-up

Candidate-facing UI handling for quota-exceeded responses is outside the scope of this backend PR and can be improved separately in a frontend follow-up.
