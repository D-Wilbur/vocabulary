# Admin Job Configuration Development Progress

## 1. Overview

The goal of this task is to add an administrator-only Job Configuration page to the RecruitDirect system.

The page is designed to allow administrators to view and update the following Job-level configuration values:

- Resume Process Limit
- Interview Limit
- Resume Process Model
- Interview Model

The implementation has been divided into five layers:

1. Frontend page
2. Frontend routing and access control
3. Frontend Store/API integration
4. Java API and business logic
5. Database changes

At the current stage, the first two layers have been completed.

---

## 2. Project Review and Scope

Before starting the implementation, I reviewed the overall project structure and identified the responsibilities of the main repositories:

```text
recruitdirect-web      Vue 3 frontend
webservice             Java Spring Boot backend
automateservice        Python AI interview service
```

There is also a design and prototype directory:

```text
design-store           UI designs and frontend prototypes
```

This task mainly affects:

```text
recruitdirect-web
webservice
```

The Python interview service is not part of the current implementation scope.

The expected final data flow is:

```text
JobConfiguration.vue
    ↓
Pinia Store
    ↓
Java REST API
    ↓
JobController
    ↓
JobService
    ↓
JobRepository
    ↓
Job Entity
    ↓
MySQL
```

---

## 3. Completed Work

### 3.1 Frontend Page Layer

A new administrator page was created:

```text
src/views/admin/JobConfiguration.vue
```

The page currently supports:

- Entering a Job ID
- Loading Job configuration
- Displaying basic Job information
- Editing Resume Process Limit
- Editing Interview Limit
- Editing Resume Process Model
- Editing Interview Model
- Required-field validation
- Positive-integer validation
- Loading state
- Saving state
- Success feedback
- Error feedback
- Responsive layout

The Job information section displays:

- Job Title
- Company
- Job Status

The model fields use a combobox so that the page can support both predefined model values and future model names returned by the backend.

#### Current Mock Data

The page currently uses mock asynchronous data for independent frontend verification.

Example mock data:

```text
Job Title: Software Engineer
Company: Avary
Status: ACTIVE

Resume Process Limit: 100
Interview Limit: 50
Resume Process Model: gpt-4o-mini
Interview Model: gpt-4o
```

The mock implementation will be replaced by real Store and API calls in the third implementation layer.

#### Frontend Page Verification

The following items were verified:

- The page compiles successfully.
- The page opens successfully in the local development environment.
- Job ID input works correctly.
- Loading a Job displays Job information.
- Loading a Job displays all four configuration fields.
- A zero limit value is rejected.
- A negative limit value is rejected.
- A decimal limit value is rejected.
- Empty model values are rejected.
- Valid values can be submitted through the mock save flow.
- Loading and saving states are displayed correctly.
- Success and error messages are displayed correctly.
- No frontend runtime error was observed.
- The page layout works on different screen widths.

---

### 3.2 Frontend Routing and Access-Control Layer

The following files were modified:

```text
src/router/MainRoutes.ts
src/router/index.ts
src/layouts/full/vertical-sidebar/sidebarItem.ts
```

The following existing files were reviewed and reused:

```text
src/layouts/full/vertical-sidebar/VerticalSidebar.vue
src/stores/authUser.ts
```

#### Formal Route

The temporary verification route:

```text
/test/job-configuration
```

was replaced by the formal route:

```text
/admin/job-configuration
```

The route includes the following metadata:

```ts
meta: {
    requiresAdmin: true
}
```

The route also inherits the Console authentication requirement from `MainRoutes`.

#### Sidebar Entry

A new sidebar item was added:

```text
Job Configuration
```

The sidebar item includes:

```ts
requiresAdmin: true
```

The existing sidebar filtering logic checks:

```text
userData.role === "admin"
```

Therefore, only administrators can see the Job Configuration menu item.

#### Route Guard

The global Vue Router guard was updated to check the Console user role before allowing access to administrator routes.

The current access-control flow is:

```text
Unauthenticated user
→ Redirect to /auth/login

Authenticated non-admin Console user
→ Redirect to /interview/joblist

Authenticated admin Console user
→ Allow access to /admin/job-configuration
```

This prevents users from bypassing the hidden sidebar item by manually entering the administrator URL.

#### Access-Control Verification

Administrator behavior was verified:

- The administrator can see the Job Configuration sidebar item.
- The administrator can access `/admin/job-configuration`.
- Other administrator-only sidebar items remain visible.

Simulated non-administrator Console behavior was also verified:

- The Job Configuration sidebar item is hidden.
- Other administrator-only sidebar items are hidden.
- Normal non-admin sidebar items remain visible.
- The frontend role-filtering logic works correctly.

#### Test Account Limitation

The provided non-administrator account belongs to the B2C customer authentication system.

The new Job Configuration page belongs to the Console/Hiring Client authentication system.

These two authentication systems use different Firebase projects and different user stores. Therefore, the provided B2C account cannot be used to validate Console administrator access control.

The current non-administrator verification was completed by locally simulating a non-admin Console role.

Final validation with a real non-admin Console/Hiring Client account remains pending.

---

## 4. Files Changed

The current frontend changes include:

```text
modified:
src/layouts/full/vertical-sidebar/sidebarItem.ts
src/router/MainRoutes.ts
src/router/index.ts

new:
src/views/admin/JobConfiguration.vue
```

Current development branch:

```text
admin-job-configuration
```

The work was completed on a separate branch and does not directly modify the main branch.

---

## 5. Current Progress

The implementation status is:

```text
[Completed] 1. Frontend page
[Completed] 2. Frontend routing and access control
[Pending]   3. Frontend Store/API integration
[Pending]   4. Java API and business logic
[Pending]   5. Database changes
```

Two of the five planned implementation layers have been completed.

The current implementation includes:

- An independent administrator page
- Four Job configuration fields
- Form validation
- Loading, saving, success, and error states
- A formal administrator route
- Sidebar integration
- Administrator-only route protection
- Local frontend verification
- Administrator and simulated non-administrator verification

The current page is still using mock data and is not yet connected to the Java backend or database.

---

## 6. Remaining Work

The following work is still pending:

- Add frontend configuration data types
- Add configuration query logic to the Pinia Store
- Add configuration update logic to the Pinia Store
- Replace mock loading with a real API request
- Replace mock saving with a real API request
- Add Java request and response DTOs
- Add Java Controller endpoints
- Add Java Service methods
- Add configuration fields to the Job entity
- Add database columns
- Add a database migration script
- Complete frontend and backend integration
- Complete final validation using real Job data
- Complete final validation using a real non-admin Console account

---

## 7. Next Steps

The next implementation layer is the frontend Store/API layer.

The planned work includes:

- Update `src/stores/jobList.ts`
- Add a method for loading administrator Job configuration
- Add a method for updating administrator Job configuration
- Define the frontend request and response types
- Replace the mock load method in `JobConfiguration.vue`
- Replace the mock save method in `JobConfiguration.vue`
- Add API error handling
- Verify the page-to-Store interaction independently

After completing the frontend Store/API layer, the next steps will be:

1. Implement Java backend endpoints
2. Implement Java business logic
3. Add Job entity fields
4. Add database migration
5. Complete end-to-end integration

---

## 8. Current Limitations

The current version can verify:

- Page layout
- Form interaction
- Input validation
- Loading and saving states
- Sidebar permissions
- Route permissions

The current version cannot yet:

- Load real Job configuration from the database
- Save real Job configuration to the database
- Apply the Resume Process Limit to the resume-processing pipeline
- Apply the Interview Limit to the interview pipeline
- Apply the selected models to the actual AI-processing workflow

These functions depend on the remaining Store, Java backend, and database layers.

---

## 9. Summary

The frontend foundation of the Admin Job Configuration feature has been completed.

Completed items include:

- Independent administrator page
- Four configuration fields
- Form validation
- Loading, saving, success, and error states
- Formal administrator route
- Administrator-only sidebar item
- Route-level administrator protection
- Administrator access verification
- Simulated non-administrator verification
- Separate Git development branch

The next stage is to connect the page to the frontend Store and real backend APIs.
