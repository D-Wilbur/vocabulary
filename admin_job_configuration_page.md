# Admin Job Configuration Page

## Requirement

I will add a new admin-only page for managing job-level processing configuration.

On this page, the admin can enter a Job ID and load the corresponding job information. The page will also display the following configuration fields:

- Resume process limit
- Interview limit
- Resume process model
- Interview model

The admin can update these values and save them to the database.

## Frontend Design

A new `Job Configuration` page will be added to the left sidebar.

The sidebar item will only be visible when the current user’s role is `admin`.

The page will contain:

- A Job ID input
- A Load button
- Basic job information, such as job title and company
- Four editable configuration fields
- A Save button
- Loading, success, and error messages

A route-level admin check will also be added, so a non-admin user cannot access the page directly through the URL.

The frontend will use the existing Axios authentication mechanism, so the Firebase token will be added to API requests automatically.

## Backend Design

Two backend APIs will be added.

### Load Job Configuration

```http
GET /job/admin/configuration/{jobId}
```

This API will return the basic job information and the four configuration values.

### Update Job Configuration

```http
PUT /job/admin/configuration/{jobId}
```

Request body:

```json
{
  "resumeProcessLimit": 50,
  "interviewLimit": 20,
  "resumeProcessModel": "model-name",
  "interviewModel": "model-name"
}
```

Both APIs will require authentication and will verify that the current HiringClient role is `admin`.

A non-admin user will not be allowed to read or update the configuration.

## Database Design

The four configuration values will be stored directly in the existing `job` table because each configuration belongs to one Job.

The following columns will be added:

```sql
resume_process_limit
interview_limit
resume_process_model
interview_model
```

The limit fields will use integer types, and the model fields will use string types.

The columns will initially allow `NULL`, so existing jobs will not be affected by the database migration.

## Implementation Scope

The implementation will include:

- New admin frontend page
- Admin-only sidebar item
- Admin route protection
- Frontend load and save logic
- Backend GET and PUT APIs
- Backend admin permission check
- Job entity update
- Database migration

This change will focus on managing and storing the configuration values.
