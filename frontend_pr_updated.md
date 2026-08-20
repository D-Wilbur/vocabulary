## Summary

This PR adds an admin Job Configuration page for viewing and updating job-level processing limits and model settings.

Administrators can load a job by Job ID, review its basic information, update its configuration, and save the changes through the backend API.

The page now also displays current resume processing and interview quota usage returned by the backend. Usage values are read-only and are shown alongside the editable limits so administrators can compare configured limits with actual usage.

## Changes

- Added the Job Configuration admin page
- Added Job ID-based configuration loading
- Displayed basic job information, including title, company, and status
- Added editable resume processing and interview limits
- Added editable resume processing and interview model fields
- Added read-only resume processing usage
- Added read-only interview usage
- Updated the Job Configuration Pinia store to support quota usage fields
- Kept quota usage out of the configuration update payload
- Added loading, validation, success, and error states
- Integrated the page with the job configuration backend endpoints

## Configuration Fields

The page supports the following editable fields:

- Resume Process Limit
- Interview Limit
- Resume Process Model
- Interview Model

The page also displays the following read-only fields:

- Resume Process Used
- Interview Used

Usage values are provided by the backend and cannot be modified from the admin page.

## Quota Usage Behavior

The admin page displays configured limits and current usage independently.

For example:

```text
Resume Process Limit: 5
Used: 5

Interview Limit: 5
Used: 5
```

Changing a configured limit does not overwrite historical usage.

For example:

```text
Before:
Interview Limit: 5
Used: 5

After updating the limit:
Interview Limit: 3
Used: 5
```

This allows administrators to reduce or increase future quota limits without modifying the number of resume or interview operations that have already been consumed.

## Screenshots

### Admin Job Configuration Page

<img width="1508" height="811" alt="image" src="https://github.com/user-attachments/assets/a40fec14-e5c6-4a64-8104-1b55f0735b32" />

### Loaded Job Configuration

<img width="1445" height="822" alt="image" src="https://github.com/user-attachments/assets/a45da9e2-bcbf-453c-9dc1-6d8afedb6b76" />

### Configuration Update

<img width="1405" height="770" alt="image" src="https://github.com/user-attachments/assets/96bef62d-e122-453d-9921-2504b1a2c73b" />

### Non-admin Access Control

<img width="707" height="275" alt=" const tokea LocalStorare qetlten（&#39;token：" src="https://github.com/user-attachments/assets/6f1a747d-637c-44c9-934c-d168815dcc03" />

### Quota Usage Display

The page displays the current usage returned by the backend next to each configured limit.

Example:

```text
Resume Process Limit: 5
Used: 5

Interview Limit: 5
Used: 5
```

[ADD SCREENSHOT: Admin Job Configuration showing Resume Process Limit/Used and Interview Limit/Used]

### Limit Update Preserves Usage

The configured limit can be changed without resetting historical usage.

Example:

```text
Interview Limit: 3
Used: 5
```

[ADD SCREENSHOT: Admin Job Configuration showing updated limit while Used remains unchanged]

## Validation

- Ran `npm run typecheck`
- Verified configuration loading using an existing Job ID
- Verified configuration updates through the backend API
- Verified that saved values persist after reloading the job
- Verified that resume processing usage is displayed correctly
- Verified that interview usage is displayed correctly
- Verified that usage values remain read-only
- Verified that updating a limit does not overwrite historical usage
- Verified that non-admin users are redirected away from the admin page

## Test Matrix

| Test case | Expected result | Verified |
|---|---|:---:|
| Admin loads an existing job configuration | Configuration is displayed | ✅ |
| Resume Process Limit is displayed | Editable limit value shown | ✅ |
| Interview Limit is displayed | Editable limit value shown | ✅ |
| Resume Process Used is displayed | Read-only usage value shown | ✅ |
| Interview Used is displayed | Read-only usage value shown | ✅ |
| Admin updates configuration | Updated values saved successfully | ✅ |
| Usage fields are excluded from update payload | Usage cannot be edited from frontend | ✅ |
| Limit is changed below current usage | Historical usage remains unchanged | ✅ |
| Saved values persist after reload | Backend values are reloaded correctly | ✅ |
| Non-admin user accesses admin page | User is redirected | ✅ |
| Frontend typecheck | Passes | ✅ |

## Related Backend Endpoints

This page uses the following backend endpoints:

```text
GET /job/configuration?jobId={jobId}
POST /job/update/configuration
```

The GET response now includes current quota usage together with the configured limits and model settings.

Example:

```json
{
  "configuration": {
    "resumeProcessLimit": 5,
    "resumeProcessUsed": 5,
    "interviewLimit": 5,
    "interviewUsed": 5,
    "resumeProcessModel": "gpt-4o-mini",
    "interviewModel": "gpt-4o"
  }
}
```

## Scope

This frontend PR is limited to the admin Job Configuration workflow.

Candidate-facing handling for quota-exceeded responses is not included in this PR and can be addressed separately.
