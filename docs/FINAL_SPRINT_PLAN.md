# Final sprint plan — 11 October 2026

**Purpose:** Freeze the last two implementation tasks before demo preparation. Each contributor has a hard three-hour cap. This plan updates the current prototype priorities; it does not claim the tasks are already implemented.

## Agreed ownership

### Laksh — small, explainable ML risk-model experiment (maximum 3 hours)

**Goal:** Determine whether a small ML model adds defensible value to the existing rule-based risk engine without destabilizing the current demo.

Timebox:
1. **20 minutes — inspect first:** Review the existing risk engine, tests, input schema, data provenance, and available labels. Identify what already exists; do not duplicate it.
2. **90 minutes — model experiment:** Only if suitable labelled observations are available, train and evaluate a shallow decision tree or logistic regression against a simple baseline.
3. **40 minutes — integration spike:** If the evaluation is meaningful, add a narrow backend integration behind a safe fallback to the existing heuristic. Keep the existing output contract stable.
4. **30 minutes — tests and handoff:** Add deterministic tests and document inputs, evaluation method, baseline comparison, limitations, and how to reproduce results.

**Acceptance criteria**
- Existing heuristic remains usable.
- The experiment is reproducible and has tests.
- Any claimed performance is based on held-out, appropriate labelled data and a stated baseline.
- Model output is clearly identified as experimental unless validation justifies stronger claims.
- A pull request and concise handoff note are ready before the time limit.

**Stop condition:** The supplied ward-exposure CSV describes historical vulnerability; it is not, by itself, a labelled dataset of flood outcomes. Do not fabricate labels or claim predictive accuracy from synthetic scenarios. If suitable labels are unavailable, use the time for a model-readiness assessment or a clearly labelled synthetic proof of integration, and keep the heuristic as the actual risk method.

### Manasvi — production frontend deployment (maximum 3 hours)

**Goal:** Publish the current frontend at a live HTTPS URL and connect it to the deployed API.

Timebox:
1. **30 minutes — inspect:** Check the production build, current AWS hosting resources, environment variables, API base URL, and mock-mode defaults.
2. **90 minutes — deploy:** Use AWS Amplify Hosting if appropriate, or reuse an existing supported host rather than creating unnecessary infrastructure.
3. **40 minutes — integrate:** Configure the production API URL and backend CORS for the deployed origin. Ensure production uses real API calls, not mock data.
4. **20 minutes — verify and document:** Test in a clean browser session; record the live URL, deployment steps, configuration variables, and known limitations.

**Acceptance criteria**
- A shareable HTTPS URL opens without a local development server.
- The production frontend targets the deployed API.
- Mock mode is disabled for the production build.
- At minimum, health/API connectivity and citizen report submission are verified; photo upload should be checked if time permits.
- Deployment steps and the URL are handed off to Mann for release verification.

**Stop condition:** Do not add custom domains, elaborate CI/CD, or new infrastructure if they threaten the three-hour limit. Never place AWS credentials or privileged secrets in frontend variables.

## Integration and release ownership

- **Laksh:** owns the ML experiment, tests, documentation, and pull request.
- **Manasvi:** owns frontend hosting, production configuration, smoke tests, deployment notes, and pull request/configuration handoff.
- **Mann:** owns integration/release approval, production end-to-end verification, and demo freeze.
- **Menaka:** updates the demo/video narrative only after the team confirms which new capabilities actually work.

Use separate branches and small pull requests. Do not push unfinished work directly to `main`. Keep the existing heuristic and the last known working deployment available until replacements are verified. After both tasks, reserve remaining time for a clean-browser rehearsal and release-blocking fixes only.

## Proposed AWS access boundaries

These are **recommended access boundaries, not IAM roles already created**. AWS access should be granted through named team identities / IAM Identity Center where available, with short-lived credentials and least privilege. Do not share the root account or long-lived access keys.

### Laksh — ML experiment
- Prefer no AWS write permissions for local modelling and evaluation.
- Read-only access to only the specific reference data objects required, if access to S3 is necessary.
- No permission to modify Lambda, API Gateway, DynamoDB production data, IAM, or the photo bucket policy.
- If model artefacts must be uploaded, use a dedicated experiment prefix and a narrowly scoped upload permission approved by Mann; do not broaden the existing runtime role.

### Manasvi — frontend hosting
- Access only to the chosen Amplify app/environment and the specific frontend deployment resources required.
- Read-only access to the existing API Gateway configuration for inspection, if needed.
- No IAM administration, no ability to change Lambda code or DynamoDB data, and no access to report-photo objects.
- Any necessary CORS change should be proposed with the exact production origin and applied by the infrastructure owner, rather than granting broad IAM permissions.

### Mann — infrastructure owner
- Keep IAM and production backend permissions with the infrastructure owner.
- Use a dedicated deployment role with only the actions and resource ARNs required for the agreed deployment; review the policy after the demo.
- Avoid wildcard administrative permissions where service/resource scoping is supported.

### IAM setup safety checklist
1. Confirm the AWS account, region, deployment service, and exact resource ARNs.
2. Create individual roles/permission sets rather than sharing credentials.
3. Require MFA and short-lived sessions where supported.
4. Do not grant `iam:*`, `AdministratorAccess`, or production data write access for convenience.
5. Test the workflow, then remove temporary permissions.
6. Do not commit policy files containing credentials or secrets.

**Current status:** No AWS IAM users, roles, policies, or permissions were changed as part of this documentation update. The exact Amplify app/resource identifiers and the team's AWS identity setup must be inspected before applying IAM changes.

## Demo freeze checklist

- [ ] ML claims match the actual evaluation; synthetic data is labelled.
- [ ] Existing heuristic remains available if the experiment is inconclusive.
- [ ] Live frontend works from a clean browser without localhost.
- [ ] Production build uses the deployed API, not mock mode.
- [ ] Report submission and persistence are smoke-tested.
- [ ] No secrets, presigned URLs, or personal information appear in the demo.
- [ ] Final demo narration reflects only verified functionality.
