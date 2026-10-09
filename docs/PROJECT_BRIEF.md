# FloodGuard --- Project Brief

## Amazon Environmental Hacks 2026 \| Project Source of Truth

**Project name:** FloodGuard\
**Category:** Environmental intelligence --- Heat & Water\
**Status:** Selected concept; implementation planning\
**Primary geography:** Mumbai, India\
**Team:** Mann, Manasvi, Laksh, Menaka\
**Document purpose:** Define the product, scope, data strategy,
architecture, AWS usage, workstreams, and delivery rules before
repository implementation begins.

------------------------------------------------------------------------

## 1. Executive summary

FloodGuard is a hyperlocal flood and waterlogging intelligence prototype
for Mumbai. It combines environmental conditions, historical ward-level
vulnerability, geographical context, and time-stamped community
observations to help users understand where flood-related risk may be
emerging and what action to take.

FloodGuard is not intended to be another weather dashboard. Its core
product loop is:

**Observe conditions → estimate and explain risk → surface hotspots →
recommend an action → incorporate new reports.**

The MVP will deliver a map-centred experience, a transparent
risk-scoring engine, a citizen incident-report workflow, and an
operational view that prioritizes reported hotspots. AWS should support
the real product workflow---data storage, API execution, scheduled
evaluation, and alerts---rather than appear as a decorative list of
services.

### Product promise

> Help people and responders make better-informed decisions about
> potential waterlogging by combining current environmental signals with
> local vulnerability and recent observations.

### Honest limitation

The first version is a decision-support prototype. Unless we obtain
suitable historical labels and validate a model, its risk output must be
described as a **heuristic risk estimate**, not a scientifically
validated flood prediction or an official warning.

------------------------------------------------------------------------

## 2. Problem statement

Heavy rainfall can produce highly localized waterlogging. City-wide
weather information does not, by itself, tell a commuter which nearby
location may be vulnerable, whether a reported hotspot is recent, or
which area a response team should inspect first.

FloodGuard aims to bridge that information gap by combining: - rainfall
conditions and forecasts where a reliable source is available; -
historical ward-level flood exposure as background vulnerability; -
geographical context and known risk locations where reliable data can be
obtained; - citizen observations with timestamps, locations, and
verification status; - a risk engine that explains why a location is
flagged.

The prototype must distinguish observed incidents from inferred risk. A
citizen report that water is accumulating is an observation; a risk
score calculated from rainfall and historical exposure is an estimate.

------------------------------------------------------------------------

## 3. Target users and key use cases

### Citizens and commuters

-   View potential waterlogging hotspots on a map.
-   See the risk level, last update time, and the factors contributing
    to it.
-   Submit a geolocated report of water accumulation or a flooded
    passage.
-   View safer alternatives or nearby options only when the routing data
    supports them.

### Responders and local coordinators

-   View a prioritized list of reported hotspots.
-   Sort or filter by risk, recency, and verification status.
-   Inspect reports and update their status.
-   See which locations may warrant checking first.

### Demo operator

-   Load a clearly labelled scenario or replay.
-   Change rainfall conditions or inject a sample incident.
-   Demonstrate the risk map and priority list updating through the
    actual application workflow.

------------------------------------------------------------------------

## 4. Product scope

### Must work for the MVP

1.  **Mumbai map view**
    -   Map with ward or location context.
    -   Clear visual distinction between background vulnerability,
        current reports, and calculated risk.
    -   Legend, timestamps, loading/error states, and accessible colour
        labels.
2.  **Ward vulnerability layer**
    -   Load the supplied CSV through the backend.
    -   Display ward-level historical exposure values.
    -   Preserve source attribution and the historical-data caveat.
3.  **Environmental conditions**
    -   Integrate a usable rainfall/forecast source if access and terms
        permit.
    -   Show source and observation/forecast time.
    -   Handle unavailable or stale data without silently presenting it
        as live.
4.  **Transparent risk engine**
    -   Produce a location/area risk category and a score.
    -   Record the contributing factors and data freshness.
    -   Separate baseline vulnerability from current conditions and
        observed incidents.
    -   Begin with a documented, testable heuristic; calibrate weights
        only when evidence supports them.
5.  **Incident reporting**
    -   Create a report with location, category, timestamp, and optional
        short description.
    -   Mark demo-generated reports as synthetic.
    -   Track statuses such as `new`, `reviewed`, and `resolved`.
    -   Include basic validation and duplicate/spam protections
        appropriate to the prototype.
6.  **Responder view**
    -   Show recent reports and calculated priorities.
    -   Make recency and verification visible.
    -   Allow a report status to be updated.
7.  **Working AWS-backed path**
    -   The UI must call the deployed API.
    -   The API must read/write the chosen data store.
    -   At least one real event or scheduled workflow should be
        demonstrated if time and access permit.
    -   Include logs and a clear demo path.
8.  **Demo and documentation**
    -   One coherent 60--90 second core story.
    -   Setup instructions, environment-variable template, architecture
        diagram, known limitations, and reproducible demo scenario.

### Stretch goals --- only after the MVP is integrated

-   Scheduled recalculation of risk when environmental data changes.
-   SNS notifications for selected high-priority conditions.
-   Better hotspot clustering or route avoidance, if usable road and
    routing data are available.
-   A small, validated ML model if suitable labelled data can be found
    quickly.
-   Bedrock-generated incident summaries, with structured facts supplied
    to the model and no unsupported claims.
-   Authentication and role separation beyond what the prototype
    demonstrably needs.
-   Additional geographic coverage beyond the selected Mumbai demo area.

### Explicitly out of scope for the first release

-   Claiming city-wide, street-level flood prediction accuracy without
    validation.
-   Presenting the ward baseline as live data or as a probability of
    flooding.
-   Pretending synthetic reports are real citizen reports.
-   Building a full emergency-dispatch platform.
-   Depending on unavailable proprietary drainage, sensor, or government
    feeds.
-   Adding AWS services purely to make the architecture diagram look
    impressive.
-   Training a complex model before the data and evaluation method
    exist.

------------------------------------------------------------------------

## 5. Data strategy and provenance

### Existing reference data

The project sources contain: - the original Mumbai Climate Action Plan
vulnerability assessment PDF; -
`floodguard_mumbai_ward_flood_exposure.csv`; -
`floodguard_mumbai_ward_flood_exposure_README.md`.

The CSV contains 24 ward records transcribed from the flood-exposure
table on printed page 112 of the report. The table's source note refers
to BMC data and Census 2011. The report also gives an aggregate exposure
figure; that aggregate is not an individual ward and is not included as
a ward row.

Use the data as a **historical vulnerability baseline**, not a current
population count, live water-level feed, street-level forecast, or
independently validated flood-probability label. Verify the
transcription against the original report before publishing exact
figures.

### Additional data to investigate

Before committing to an external feed, verify: - availability and
geographic resolution; - update frequency and timestamp semantics; -
access limits, attribution, and permitted use; - whether the API works
without a paid key; - whether it returns observed rainfall, forecast
rainfall, or both; - failure behaviour and whether a cached last-known
value can be shown safely.

Potential categories include public weather/precipitation APIs, open map
data, elevation data, and authoritative flood or waterlogging records.
These are candidate sources, not confirmed integrations. Record the
selected source and its limitations in `docs/DATA_SOURCES.md`.

### Data trust rules

Every environmental value should carry, where applicable: - source
identifier; - location or geographic unit; - event/observation time; -
retrieval or update time; - unit; - whether it is observed, forecast,
historical, or simulated; - freshness/validity status.

If live data fails, show the failure or a clearly labelled cached/sample
state. Never quietly substitute sample values and call them live.

------------------------------------------------------------------------

## 6. Risk-engine design

The first implementation should be explainable and deterministic. A
possible conceptual formulation is:

`risk = f(rainfall signal, baseline vulnerability, recent verified reports, location context)`

This is a design outline, not a validated equation. The team must
document the actual inputs, normalization, weights, thresholds,
missing-data behaviour, and limitations in code and documentation.

### Required principles

1.  **Do not double-count the same signal.** For example, a
    report-derived hotspot score and a separate report-count feature may
    represent overlapping evidence.
2.  **Do not equate ward exposure with event probability.** The CSV
    describes people potentially exposed near flood-risk locations,
    using historical population data.
3.  **Recency matters.** An old unresolved report must not carry the
    same evidential weight as a new report.
4.  **Verification matters.** A report awaiting review must be
    distinguishable from a verified observation.
5.  **Explain the score.** Show reasons such as elevated rainfall
    signal, high historical ward exposure, or recent verified reports.
6.  **Handle missing data explicitly.** If rainfall data is unavailable,
    the application must not pretend the full risk calculation is
    current.
7.  **Test edge cases.** Empty reports, stale feeds, invalid
    coordinates, duplicate reports, and API failures need defined
    behaviour.

### ML decision

ML is not a requirement by itself. Do not claim the heuristic is a
trained model. Add ML only if a suitable dataset, target label,
evaluation split, baseline comparison, and measurable benefit can be
established within the build window. A transparent heuristic is better
than a fake or unvalidated "AI prediction."

------------------------------------------------------------------------

## 7. Proposed application architecture

### High-level flow

``` text
External rainfall / forecast source
                 |
                 v
     Ingestion or scheduled refresh
                 |
                 v
       AWS Lambda processing
                 |
        +--------+---------+
        |                  |
        v                  v
Historical ward CSV    Incident records
(S3/static reference)  (DynamoDB)
        |                  |
        +--------+---------+
                 |
                 v
        Risk calculation layer
                 |
                 v
        API Gateway HTTP API
                 |
                 v
        React web application
          |              |
          v              v
      Public map     Responder view
          |
          v
  Citizen incident submission
```

The exact implementation order may differ. Keep interfaces small and
agree them before parallel development.

### Frontend

-   React with Vite.
-   TypeScript is preferred if the team can move quickly with it;
    otherwise use JavaScript consistently rather than mixing styles.
-   Tailwind CSS or the team's established CSS approach.
-   Leaflet with OpenStreetMap-based tiles, subject to provider terms
    and usage limits.
-   A charting library only if a chart materially improves the main
    workflow.
-   Frontend environment variables must not contain secrets.

### Backend and API

-   AWS API Gateway HTTP API for public application endpoints.
-   AWS Lambda for request handling and risk calculation.
-   Python is a reasonable choice for the risk/data-processing
    functions; Node.js is also viable if it reduces team integration
    cost. Pick one backend runtime for the MVP unless there is a clear
    reason to split.
-   Validate request payloads, coordinates, enumerated values, and
    lengths.
-   Return explicit errors and timestamps; do not leak internal errors
    or secrets.
-   Configure CORS for the deployed frontend origin.

### Storage

-   **Amazon S3:** source datasets and any static reference files; keep
    original and processed data clearly separated.
-   **Amazon DynamoDB:** incident reports, report status, and latest
    computed risk records if persistence is needed.
-   The ward CSV can initially be bundled with the backend or loaded
    from S3. Do not create a database table merely to copy a small
    static CSV unless a real query/access need justifies it.

### Event-driven workflow

-   **Amazon EventBridge:** scheduled refresh/recalculation if the
    selected environmental source and demo require it.
-   **AWS Lambda:** perform the refresh and recompute risk.
-   **Amazon SNS:** optional alerts for a defined threshold and
    recipient/channel that can actually be tested.
-   **Amazon CloudWatch:** logs, errors, and basic operational
    visibility.

EventBridge and SNS are stretch goals unless the scheduled/event
workflow is implemented and demonstrated end-to-end.

### Security and configuration

-   Use IAM roles with least privilege for Lambda access.
-   Use environment variables for non-secret configuration.
-   Never commit API keys, AWS credentials, tokens, or real personal
    information.
-   Use AWS Secrets Manager only if a real secret-management need exists
    and there is enough time to configure it correctly.
-   Add input validation, request-size limits, basic rate limiting where
    feasible, and safe error messages.
-   Do not collect names, phone numbers, or precise personal details
    unless essential to the demo.

### AWS service selection rule

A small working architecture is better than a large fictional one. The
MVP target is API Gateway + Lambda + appropriate storage, with S3 for
reference data. Add EventBridge, SNS, or other services only when their
associated workflow exists, can be tested, and improves the product.

------------------------------------------------------------------------

## 8. Suggested API contract

Agree the request/response shape before independent implementation.
Names may change once the repository is created, but changes must be
communicated.

  -----------------------------------------------------------------------
  Endpoint                            Purpose
  ----------------------------------- -----------------------------------
  `GET /health`                       Deployment and API health

  `GET /wards`                        Ward baseline and metadata

  `GET /risk`                         Current risk results with
                                      timestamps and explanations

  `GET /reports`                      Recent reports with filters as
                                      feasible

  `POST /reports`                     Validate and create an incident
                                      report

  `PATCH /reports/{id}`               Update report status in the
                                      responder workflow
  -----------------------------------------------------------------------

Every response should have a predictable JSON shape. Include a sample
response for each endpoint in `docs/API_CONTRACT.md` or the README.
Avoid having frontend and backend developers independently invent
incompatible payloads.

------------------------------------------------------------------------

## 9. Repository structure

``` text
FloodGuard/
├── frontend/
├── backend/
├── data/
│   ├── reference/
│   │   ├── floodguard_mumbai_ward_flood_exposure.csv
│   │   └── floodguard_mumbai_ward_flood_exposure_README.md
│   └── sample/
├── docs/
│   ├── PROJECT_BRIEF.md
│   ├── ARCHITECTURE.md
│   ├── DATA_SOURCES.md
│   ├── API_CONTRACT.md
│   ├── DEMO_SCRIPT.md
│   └── LIMITATIONS.md
├── .env.example
├── .gitignore
└── README.md
```

The original assessment PDF can remain in the ChatGPT Project sources
and be referenced from documentation. Only add the full PDF to Git if
repository size, licensing, and distribution considerations have been
checked. The CSV and its README should be version-controlled.

### Git hygiene

-   Commit `.env.example`; ignore `.env` and credential files.
-   Keep generated build outputs, caches, and virtual environments out
    of Git.
-   Use clear, small commits and branches or pull requests for parallel
    changes.
-   Do not commit AWS access keys or account-specific secrets.
-   Make a clean clone and setup test before submission.

------------------------------------------------------------------------

## 10. Team responsibilities --- technical workstreams

The team has four people. Work is divided by technical workstream, with
independent implementation against agreed interfaces. The aim is to let
everyone work uninterrupted for hours without waiting on another person.
Dependencies are reduced, not eliminated: shared contracts and scheduled
integration checkpoints keep the work compatible.

### Mann --- Platform architecture, AWS/backend integration, release owner

Primary responsibilities:

- Define API contracts and shared data models with the team.
- Own the backend and AWS application path: API Gateway, Lambda, IAM,
  storage access, deployment, and operational logging as selected.
- Connect the risk-engine output and stored reports to API responses.
- Maintain environment configuration, integration checkpoints, and the
  final deployed build.
- Keep the deployed path secure and ensure the demo reflects actual
  implemented behaviour.

Independent work and proof:

- Build and test endpoints with sample requests and sample data before
  the data pipeline or frontend is ready.
- Demonstrate a working health endpoint and a documented API response.

Integration checkpoints:

- **Checkpoint 0:** Agree endpoint names, request/response examples,
  identifiers, timestamps, error formats, and the selected runtime.
- **Checkpoint 1:** Share a working backend skeleton and API examples;
  frontend development must be able to continue against the contract.
- **Checkpoint 2:** Connect the risk engine and persistence through the
  agreed interface; run a joint request-to-response test.
- **Checkpoint 3:** Deploy the minimal AWS path early and have at least
  one end-to-end frontend → API → storage → API → frontend flow working.
- **Checkpoint 4:** Run the release checklist and provide Menaka with a
  stable build and confirmed facts for the video.

### Manasvi --- Data pipeline, environmental research, risk intelligence

Primary responsibilities:

- Audit the ward CSV and document provenance and limitations.
- Investigate and test external rainfall and geographic data sources;
  record whether each source is actually accessible and usable.
- Build a reproducible data-normalization or refresh path for the chosen
  sources.
- Implement the explainable risk calculation and its tests in agreement
  with the team.
- Define missing/stale-data behaviour and provide reusable test fixtures.
- Document the score inputs, units, assumptions, and limitations.

Independent work and proof:

- Work with the supplied CSV and local/sample environmental inputs.
- Deliver a documented risk function that accepts a defined input and
  returns a score, level, explanation, timestamp/freshness fields, and
  relevant uncertainty or missing-data status.
- Provide tests and sample input/output files without requiring the live
  API or map to be running.

Integration checkpoints:

- **Checkpoint 0:** Agree the risk-engine input/output schema and what
  counts as observed data, forecast data, historical baseline, or a
  labelled simulation.
- **Checkpoint 1:** Deliver cleaned ward data, provenance notes, and
  representative fixtures; the frontend can use the same fixtures.
- **Checkpoint 2:** Demonstrate deterministic risk calculations and
  tests locally; agree the scoring interface with Mann.
- **Checkpoint 3:** Run the risk engine through the backend API and
  verify the map shows the same risk level, reasons, and freshness.
- **Checkpoint 4:** Confirm the exact data sources, caveats, and claims
  that can safely appear in Menaka's video.

### Laksh --- Geospatial frontend, user experience, responder workflow

Primary responsibilities:

- Build the map-centred interface and layer/legend design.
- Implement ward vulnerability display, incident markers, risk status,
  explanations, and freshness indicators.
- Build the report-submission and responder-review interfaces against
  the agreed API contract.
- Handle loading, empty, error, offline, and stale-data states.
- Keep the main workflow clear and visually polished.

Independent work and proof:

- Build against mock API responses and sample map data so work does not
  block on the deployed backend or finished risk engine.
- Demonstrate a working map, ward selection, risk details, report form,
  and responder list using labelled mock data.

Integration checkpoints:

- **Checkpoint 0:** Agree API response shapes, ward identifiers,
  coordinate conventions, and the states the UI must display.
- **Checkpoint 1:** Show the map and main screens using mock responses;
  get an early usability review before adding polish.
- **Checkpoint 2:** Replace mock risk results with the agreed risk-engine
  response shape while keeping the same UI contract.
- **Checkpoint 3:** Connect the deployed API; verify report submission,
  persistence, map/list refresh, and visible error handling end-to-end.
- **Checkpoint 4:** Freeze the UI for recording; remove dead controls and
  confirm every interaction shown in the video works in the release build.

### Menaka --- Documentation and YouTube demo video

Primary responsibilities:

- Produce the project documentation using verified information from the
  team, including problem, architecture, data sources, limitations, and
  setup/demo instructions.
- Create the presentation and supporting visual assets as required.
- Produce a demonstration video intended for upload to YouTube, with an
  AI voice-over explaining the problem, the application, the workflow,
  the role of AWS, and the prototype's limitations.
- Plan the video narrative, screen capture, scene order, captions, and
  final quality check.
- Ensure the video never presents simulated inputs, mock data, or
  unvalidated risk scores as live or proven predictions.

Independent work and proof:

- Start with the project brief, storyboard, script draft, visual style,
  and a list of scenes before the full application is ready.
- Prepare reusable title cards and explanatory diagrams using the
  agreed architecture and verified facts.
- Keep placeholders clearly marked until a real build or screenshot is
  available; do not invent results to fill a scene.

Integration checkpoints:

- **Checkpoint 0:** Agree the intended audience, video length/format,
  core story, AI voice-over approach, and required YouTube deliverable.
- **Checkpoint 1:** Share the storyboard and narration draft with the
  team so technical claims can be checked before recording.
- **Checkpoint 2:** Review an early rough cut using mock/sample scenes;
  label any simulated workflow explicitly and keep replaceable scenes
  easy to update.
- **Checkpoint 3:** Capture the real integrated application after the
  end-to-end workflow works; Mann verifies AWS claims and Manasvi verifies
  data/risk claims before final narration is locked.
- **Checkpoint 4:** Publish-ready review: confirm video/audio quality,
  readable labels, accurate captions, no secrets or personal data on
  screen, working YouTube title/description, and no unsupported claims.
  Upload/publish only when the team has approved the final version.

### Shared ownership

- Each workstream owner is accountable for progress and a testable
  deliverable, not exclusive ownership of every related line of code.
- Every person communicates blockers early and keeps their work in a
  separate branch or clearly separated files where practical.
- The team reviews interfaces and integration results at checkpoints;
  routine work does not require everyone to be online together.
- A feature is not considered complete merely because it works in a
  local branch: it must pass its workstream checks and the relevant
  integration test.
- Menaka can prepare the narrative early, but final video claims and
  screen captures must match the integrated release build.

If actual availability or strengths differ, revise assignments before
implementation rather than silently leaving a workstream unowned.

------------------------------------------------------------------------

## 11. Integration checkpoints and delivery plan

The team works independently for most of each work period. Integration
is scheduled at named checkpoints rather than happening continuously in
meetings. Each checkpoint has a concrete artifact, an acceptance test,
and a clear exit condition. Share progress asynchronously through Git,
short notes, and sample inputs/outputs.

### Checkpoint 0 --- Contract freeze (before parallel implementation)

**Everyone contributes; Mann coordinates.**

- Confirm the repository structure, local setup, branch/commit approach,
  and initial demo area.
- Agree the API contract, ward identifier format, coordinate convention,
  risk-engine input/output schema, and error/freshness fields.
- Choose how the frontend will mock the API and how the risk engine will
  run locally.
- Confirm which data sources are verified, which are only candidates,
  and how simulated data will be labelled.
- Agree Menaka's video audience, story, AI voice-over, and deliverable.

**Exit condition:** every workstream can start without waiting for
another person to write code. Contracts and example JSON/CSV fixtures
are committed to the repository.

### Checkpoint 1 --- Independent skeletons

- **Mann:** health endpoint and initial API skeleton run locally; sample
  requests and response examples are documented.
- **Manasvi:** ward data is audited; provenance notes and initial risk
  fixtures are available; the scoring function has a defined interface.
- **Laksh:** map and core screens render from mock data using the agreed
  response shape.
- **Menaka:** storyboard, script outline, documentation skeleton, and
  visual style are shared for review.

**Exit condition:** each person can demonstrate their work without
needing the other workstreams to be finished.

### Checkpoint 2 --- Independently testable deliverables

- **Mann:** API contract tests or repeatable request tests pass.
- **Manasvi:** risk function returns explainable results and passes
  basic tests for normal, missing, stale, and boundary inputs.
- **Laksh:** the main UI flow works with fixtures, including empty/error
  states and clear labels for simulated data.
- **Menaka:** the storyboard and narration draft are reviewed for
  technical accuracy; a rough cut or sample scene establishes the video
  format and AI voice-over quality.

**Exit condition:** each owner hands over a small reproducible artifact
(code, tests, fixture, screen recording, script, or document) and notes
any limitations. Do not wait for perfect polish.

### Checkpoint 3 --- First integration (local end-to-end slice)

- Connect the risk-engine output to the backend through the agreed
  contract.
- Connect the frontend to the API; preserve a mock mode for independent
  development and fallback testing.
- Submit a test incident and verify it is stored and returned to the
  interface, using the selected storage implementation or a clearly
  labelled local substitute if AWS is not ready yet.
- Compare the risk details shown in the UI against the risk-engine
  output; check identifiers, units, reasons, and timestamps.
- Menaka updates the storyboard to match what the real build can show.

**Exit condition:** one local workflow works from displayed ward/risk
information through incident submission and back to the refreshed UI.

### Checkpoint 4 --- AWS integration and deployed slice

- Deploy the smallest useful AWS path before adding optional services.
- Verify frontend → API Gateway → Lambda → selected storage → API
  response → frontend using a real test record.
- Check IAM scope, logs, error responses, configuration, and secrets.
- Test any scheduled refresh or alert end-to-end before claiming it is
  implemented; omit optional services that do not fit the time budget.
- Record which data is live, cached, historical, or simulated.
- Capture the release candidate and send verified technical/data facts
  to Menaka for the final video.

**Exit condition:** the deployed end-to-end slice works from a clean
browser/session, and the team can reproduce the test.

### Checkpoint 5 --- Demo freeze and YouTube video sign-off

- Stop adding features; only fix release-blocking defects.
- Run the complete demo from a clean browser/session and test invalid
  reports, empty reports, stale/missing environmental data, and network
  failures where relevant.
- Verify every visible control works and every simulation is labelled.
- Menaka records/captures the real release build, finalizes the AI
  voice-over, checks captions and visual readability, and prepares the
  YouTube title/description.
- Mann verifies infrastructure/AWS statements; Manasvi verifies data,
  score explanations, and limitations; Laksh verifies the recorded UI
  reflects the final build.
- Review the final video together before upload. Keep a local copy of
  the approved export and the script in the repository/docs as suitable.

**Exit condition:** the application demo and video tell the same story,
all claims are supported, and the team approves the publish-ready video.

### Integration rules

- Do not wait until the final hours to connect the branches.
- If an upstream dependency is late, continue with the agreed mock or
  fixture; never silently change the contract.
- A contract change must be communicated and reflected in fixtures,
  tests, and documentation.
- Use small commits and integrate at each checkpoint; reserve explicit
  time for integration and video review.
- The core path is map → risk explanation → incident report → refreshed
  view. Optional alerts, routing, ML, or extra AWS services come later.

------------------------------------------------------------------------

## 12. Core demo story

Target one polished short sequence for the application walkthrough; Menaka will produce a YouTube video with AI voice-over. The final video length should be agreed at Checkpoint 0. A 60--90 second core sequence can serve as the backbone:

1.  Open the Mumbai map and show historical ward vulnerability with a
    clear legend.
2.  Show the environmental signal and when it was last updated.
3.  Trigger a clearly labelled rainfall scenario or use a real feed that
    is demonstrably live.
4.  Show the risk estimate change and explain which inputs caused the
    change.
5.  Submit a sample incident such as "water accumulating near Gate 2."
6.  Show the report on the map and in the responder queue, with its
    timestamp and verification state.
7.  Show the updated priority or suggested action.
8.  End with the limitation and value proposition stated accurately:
    FloodGuard supports local decisions; it does not replace official
    warnings or emergency services.

The demo should use the actual integrated application. A scripted
scenario is acceptable if labelled as a simulation; fabricated live data
is not.

------------------------------------------------------------------------

## 13. Quality, evaluation, and acceptance criteria

The MVP is ready when: - The application can be started from documented
instructions. - The deployed frontend can call the deployed backend. -
The ward baseline is traceable to its source and clearly labelled
historical. - Risk outputs are reproducible for fixed inputs. - Each
displayed risk result has an explanation and timestamp/freshness
state. - A report can be created, stored, displayed, and reviewed. -
Invalid submissions and missing environmental data fail safely. - At
least one coherent end-to-end demo works without manually editing
database records mid-demo. - No secrets are committed. - The README
explains setup, architecture, data sources, demo steps, and limitations.

For judging, prioritize: 1. A real environmental problem and clear
impact pathway. 2. One complete, reliable, visually clear workflow. 3.
AWS services that enable actual product behaviour. 4. Evidence-based
data handling and honest claims. 5. Strong usability and a clean demo.
6. Additional features only after the core works.

The previous First Commit result taught us that a functioning app alone
is not enough: technical integration, execution polish, demo clarity,
and usability all matter. Do not optimize for service count.

------------------------------------------------------------------------

## 14. Risks and mitigations

  -----------------------------------------------------------------------
  Risk                                Mitigation
  ----------------------------------- -----------------------------------
  Historical baseline mistaken for    Label source, year, geography, and
  current prediction                  intended use in UI and docs

  External API limits or outages      Test early; cache where permitted;
                                      show stale/unavailable status; keep
                                      labelled demo fixtures

  Insufficient labels for ML          Use an explainable heuristic; do
                                      not claim a trained model

  Scope expands too far               Protect the core map → risk →
                                      report → response workflow

  AWS configuration consumes build    Deploy a minimal path early and
  time                                test it before adding services

  Teammates build incompatible        Freeze the API contract early and
  interfaces                          use mock responses

  Last-minute integration failure     Continuous integration checkpoints
                                      and a feature freeze

  Demo implies official emergency     State prototype limitations and
  advice                              direct users to official guidance
                                      for emergencies

  Secrets or personal data enter Git  `.gitignore`, environment
                                      templates, least privilege, and
                                      data minimization
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 15. Decisions log

### Decided

-   FloodGuard is the selected project direction.
-   The initial focus is Mumbai.
-   The existing ward CSV is a historical vulnerability baseline.
-   The product should combine environmental signals, vulnerability, and
    reports to support action.
-   The project must demonstrate meaningful AWS usage, not merely AWS
    hosting.
-   Team responsibilities should be split across four technical/documentation workstreams rather than the prior feature-by-feature model.
-   Menaka owns the YouTube demo video with AI voice-over, with team review of technical claims before upload.
-   Workstreams should operate independently against agreed contracts, with explicit integration checkpoints.
-   The first release should prioritize one integrated vertical slice.

### To decide before or during the first implementation milestone

-   Exact demo ward/area.
-   External rainfall source and any geographic data source.
-   Backend runtime: Python or Node.js.
-   Exact risk inputs, normalization, weights, and thresholds.
-   Whether EventBridge/SNS fit the time budget.
-   Whether any ML component is justified by data and evaluation.
-   Deployment method and final AWS region.
-   Whether authentication is needed for the demo or can be safely
    deferred.

Record any change to a decided item here or in a dated decision log so
all teammates work from the same plan.

------------------------------------------------------------------------

## 16. Operating rules for the project

-   Build the smallest end-to-end path first.
-   Verify data access before designing a feature around it.
-   Keep observed facts, forecasts, historical baselines, and
    simulations visibly distinct.
-   Never claim an unimplemented service or unvalidated model.
-   Every AWS service must have a clear purpose and a tested path.
-   Agree interfaces before parallel implementation.
-   Prioritize reliability, explainability, and a compelling demo over
    feature count.
-   Treat this document as the project source of truth; update it when
    material decisions change.

**Next step:** create the GitHub repository, add this document as
`docs/PROJECT_BRIEF.md`, copy the CSV and README into `data/reference/`,
and create the initial README, `.gitignore`, and `.env.example`. Then
complete Checkpoint 0 and begin the independent skeletons.
