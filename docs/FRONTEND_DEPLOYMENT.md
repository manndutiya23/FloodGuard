# FloodGuard frontend deployment runbook — AWS Amplify Hosting

**Last updated:** 11 October 2026  
**Owner:** Manasvi  
**Repository:** [manndutiya23/FloodGuard](https://github.com/manndutiya23/FloodGuard)

## Current deployment status

At the time this runbook was first created, the Amplify app had **not yet been created**. The production website URL, Amplify app ID, production API URL, and end-to-end smoke-test results therefore remain unconfirmed. Update the deployment record at the end of this document only after each item is verified in the AWS console or browser.

This file documents the intended setup; it is **not evidence that a deployment or production test has succeeded**.

## Scope

Deploy the existing React, TypeScript, and Vite frontend from the repository's `frontend/` directory to AWS Amplify Hosting. The backend already runs separately behind API Gateway and Lambda/FastAPI.

This task covers frontend hosting and frontend-to-API configuration. It does not require creating a new backend, database, Lambda function, API, or custom domain. Do not make backend or IAM changes as part of this frontend deployment unless the infrastructure owner has specifically approved them.

## 1. Prerequisites and local build

1. Confirm that the GitHub repository is `manndutiya23/FloodGuard` and the deployment branch is `main`.
2. From PowerShell, open the repository's `frontend` directory.
3. Install the lockfile-pinned dependencies and build the production bundle:

   ```powershell
   npm.cmd ci
   npm.cmd run build
   ```

   On Windows PowerShell, use `npm.cmd` if the `npm.ps1` wrapper is blocked by the local execution policy. Do not weaken the machine-wide PowerShell execution policy just to run npm.

4. Confirm that the build finishes successfully and creates `frontend/dist/`.
5. Obtain the exact API Gateway Invoke URL from the backend/infrastructure owner. Do not guess the URL or its stage suffix.

## 2. Create the Amplify Hosting app

1. Sign in to the AWS Console using your own approved IAM identity and MFA. Confirm the AWS account and select the appropriate Region.
2. Open [AWS Amplify Console](https://console.aws.amazon.com/amplify/home).
3. Choose **Create new app** / **Host web app** and select GitHub as the Git provider.
4. Authorize Amplify to access the repository. Prefer granting access only to `manndutiya23/FloodGuard`, rather than all GitHub repositories.
5. Choose repository `FloodGuard` and branch `main`.
6. Enable **My app is a monorepo** and set the app root/path to exactly `frontend`. Do not enter `frontend/src` or a local Windows path.
7. Continue to the build settings and review the values in the next section before starting the deployment.

For a new app created from the Amplify console, Amplify should set `AMPLIFY_MONOREPO_APP_ROOT=frontend` automatically. If it is missing in a later configuration, set that variable to `frontend` in the Amplify app's environment variables.

## 3. Build configuration

Use these settings for the Vite frontend:

| Setting | Value |
| --- | --- |
| Git repository | `manndutiya23/FloodGuard` |
| Branch | `main` |
| Monorepo app root | `frontend` |
| Install command | `npm ci` |
| Build command | `npm run build` |
| Build artifact directory | `dist` |

If Amplify asks for a YAML build specification rather than individual settings, use the following monorepo configuration and ensure `AMPLIFY_MONOREPO_APP_ROOT` has the same value as `appRoot`:

```yaml
version: 1
applications:
  - appRoot: frontend
    frontend:
      phases:
        preBuild:
          commands:
            - npm ci
        build:
          commands:
            - npm run build
      artifacts:
        baseDirectory: dist
        files:
          - '**/*'
      cache:
        paths:
          - node_modules/**/*
```

Do not add a root-level `amplify.yml` blindly. A repository build specification overrides build settings saved in the Amplify console, so use one source of configuration and verify it matches the settings above.

Click **Save and deploy**. Watch the build log and confirm that all build stages succeed. If it fails, fix the build error before treating the site as deployed.

## 4. Production environment variables

In the Amplify app, open **Hosting → Environment variables → Manage variables** and configure:

| Variable | Production value | Notes |
| --- | --- | --- |
| `VITE_API_BASE_URL` | Exact API Gateway Invoke URL supplied by the backend owner | Include any required API stage suffix. Do not use the local `/api` proxy path. |
| `VITE_USE_MOCKS` | `false` | Must be the literal text `false` to disable frontend mock mode. |

The repository's `VITE_API_PROXY_TARGET` is for the local Vite development proxy. It is not needed for Amplify production hosting.

Save the variables and trigger a new deployment if the console does not start one automatically. Vite variables are embedded into the browser bundle during build, so the correct values must be present when the production build runs.

**Never store AWS access keys, passwords, tokens, or other secrets in `VITE_*` variables.** These values are exposed to browser users in the built frontend. The API URL is configuration, not a secret.

## 5. API CORS handoff

After the first successful Amplify deployment:

1. Copy the website's exact HTTPS **origin** (scheme plus hostname only, without a route such as `/report`).
2. Send that origin and the required API URL to the backend/infrastructure owner.
3. Ask the owner to allow the origin in the live API Gateway/FastAPI configuration as applicable.
4. If the browser reports CORS errors during photo upload, ask the owner to check the relevant S3 bucket CORS configuration as well.

Do not use a wildcard origin as a shortcut. Do not change API Gateway, Lambda, IAM, DynamoDB, or S3 settings yourself unless the infrastructure owner has explicitly assigned and approved that work.

## 6. Single-page application routes

If the home page loads but direct navigation or browser refresh on a frontend route (for example, `/report` or `/responder`) returns 404, review **Hosting → Rewrites and redirects** in Amplify. Add the official Amplify single-page-app rewrite to serve `/index.html` with status 200 for frontend routes. Preserve existing rules and avoid rewriting real static asset requests incorrectly.

AWS reference: [Redirects and rewrites examples](https://docs.aws.amazon.com/amplify/latest/userguide/redirect-rewrite-examples.html).

## 7. Production smoke test

Test the deployed HTTPS site in a clean/incognito browser after the environment variables and CORS configuration are in place. Mark each check only after it succeeds.

- [ ] Homepage loads without a blank screen or browser-console build errors.
- [ ] The frontend indicates the live API is connected and does not indicate mock mode.
- [ ] Network requests to the configured API succeed for health, wards, weather, risk, and reports.
- [ ] The report list is populated by the live API, not mock fixtures.
- [ ] A harmless text-only test report can be submitted.
- [ ] The report appears in the live report list and remains after a page refresh.
- [ ] If time permits, a small photo upload succeeds through the presigned-upload flow.
- [ ] Direct refresh of app routes works, if the app uses client-side routes.
- [ ] No credentials, personal information, or other secrets are visible in the frontend or demo.

Use harmless test data and coordinate cleanup of any test report with the backend owner. Do not run demo seeding scripts against production as part of a smoke test unless the team explicitly approves that operation.

## 8. Troubleshooting

| Symptom | What to check |
| --- | --- |
| Amplify build fails | Read the first meaningful build error; confirm repository branch, app root `frontend`, lockfile, `npm ci`, `npm run build`, and artifact directory `dist`. |
| Site loads but shows mock data | Confirm `VITE_USE_MOCKS=false` in Amplify environment variables and trigger a fresh build. |
| API requests fail with CORS errors | Confirm the browser's exact HTTPS origin has been allowed by the API Gateway/FastAPI owner; inspect Network details. |
| API returns 404 | Verify `VITE_API_BASE_URL` includes the correct base URL/stage and does not contain an unintended route suffix. |
| Report submission fails | Inspect the failing Network request and response; confirm report endpoint availability and CORS with the backend owner. |
| Photo upload fails while API calls work | Check the presigned-upload request and ask the backend owner to verify S3 bucket CORS and upload constraints. |
| Refreshing a nested route returns 404 | Check the SPA rewrite configuration; retain existing rewrite rules. |

## 9. Subsequent deployments

When Amplify is connected to GitHub's `main` branch, new commits merged into that branch normally trigger another build and deployment. Before merging frontend changes, run the local build and review the pull request. After deployment, inspect the Amplify build result and repeat the smoke tests for any changed critical flow.

Keep deployment documentation updated when the website URL, connected branch, API URL configuration approach, or verified smoke-test results change. Do not put credentials or secret values into this file.

## 10. Deployment record

Fill this record in only after confirming the information. Do not mark the deployment complete until the live site and the required smoke tests have been checked.

| Item | Verified value / status |
| --- | --- |
| Amplify app name / ID | Pending — fill after app creation |
| AWS Region | Pending — fill after app creation |
| Connected repository and branch | Expected: `manndutiya23/FloodGuard`, `main`; confirm in Amplify |
| Monorepo app root | Expected: `frontend`; confirm in Amplify |
| Amplify HTTPS URL | Pending — fill after successful deployment |
| Production API URL | Pending — obtain from backend owner; do not add credentials |
| Production mock mode disabled | Pending — verify environment variable and live UI |
| API CORS confirmed for Amplify origin | Pending — backend owner confirmation |
| Report submission and persistence | Pending — record actual smoke-test result |
| Photo upload | Pending / not tested until verified |
| Last verified build / date | Pending — fill after successful build |

## Official AWS references

- [Configure Amplify monorepo build settings](https://docs.aws.amazon.com/amplify/latest/userguide/monorepo-configuration.html)
- [Configure Amplify environment variables](https://docs.aws.amazon.com/amplify/latest/userguide/setting-env-vars.html)
- [Amplify build specification reference](https://docs.aws.amazon.com/amplify/latest/userguide/yml-specification-syntax.html)
- [Amplify redirects and rewrites](https://docs.aws.amazon.com/amplify/latest/userguide/redirect-rewrite-examples.html)
