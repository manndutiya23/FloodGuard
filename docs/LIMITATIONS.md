# FloodGuard Limitations and Responsible Use

**Project:** FloodGuard — Mumbai Hyperlocal Flood Intelligence  
**Status:** Prototype development  
**Version:** 1.0

## 1. Purpose

This document defines the known limitations of FloodGuard, the claims its outputs can support, and the precautions required when displaying environmental risk information.

FloodGuard is being developed as a prototype to help users understand historical flood exposure, interpret available environmental signals, and view reported incidents at the ward level.

The application must communicate uncertainty honestly. A feature must not be described as operational, live, validated, or production-ready until its implementation and supporting evidence have been verified.

## 2. Historical ward exposure data

FloodGuard uses a reference dataset transcribed from a ward-level table in the Mumbai Climate Action Plan's *Climate & Air Pollution Risks and Vulnerability Assessment* report.

The dataset contains the estimated population potentially exposed within a 250-metre buffer and the corresponding percentage of ward population.

### Limitations

- The underlying population information is associated with Census 2011 and is not a current population count.
- The figures describe potential historical exposure, not the number of people currently experiencing flooding.
- The 250-metre buffer represents the source assessment's methodology. It is not a live flood boundary.
- The figures do not independently establish the probability, timing, depth, or severity of a future flood.
- The transcribed values require verification against the original report before being treated as confirmed figures.

### Mitigation

- Display both the population count and percentage where available.
- Label these values as historical exposure estimates.
- Identify the source and relevant population-data year.
- Preserve the distinction between historical exposure and current risk.
- Record and resolve discrepancies found during source verification.

## 3. Current environmental data availability

FloodGuard's ability to assess current conditions depends on the availability and quality of suitable environmental data.

Potential inputs include rainfall observations, rainfall forecasts, historical flood records, and geographic information. These inputs are not interchangeable.

### Limitations

- A rainfall observation describes rainfall that has occurred during a particular period.
- A rainfall forecast describes expected future conditions and may be uncertain.
- Historical incident records do not establish that an incident is occurring now.
- Data availability, geographic coverage, update frequency, and access conditions depend on the chosen provider.
- A planned integration must not be represented as a functioning integration before it has been implemented and tested.

### Mitigation

- Record the source and timestamp of environmental inputs.
- Distinguish observed values from forecast values.
- Display data freshness or availability status where relevant.
- Clearly label simulated inputs and simulated outputs.
- Do not describe FloodGuard as providing live flood monitoring until the relevant data pipeline is operational and verified.

## 4. Risk scoring and prediction accuracy

The initial FloodGuard risk engine is intended to use an explainable heuristic: a documented set of rules that combines suitable inputs into a risk assessment.

### Limitations

- A heuristic score is not automatically a statistically calibrated flood probability.
- Historical exposure figures alone cannot establish whether flooding will occur.
- The accuracy of the output depends on the quality, coverage, recency, and relevance of its inputs.
- The initial scoring method has not been established as a validated flood-prediction model.
- Without suitable historical event labels and systematic evaluation, the team cannot claim a particular prediction accuracy or demonstrate that the score reliably predicts real-world flooding.

### Mitigation

- Document the scoring rules and explain the reasons behind each assessment.
- Show which available inputs contributed to a result.
- Identify missing, stale, or simulated inputs.
- Avoid presenting arbitrary numerical scores as percentages of flood probability.
- Evaluate the method against suitable historical observations if reliable evaluation data becomes available.
- Describe the output as a heuristic risk assessment unless validation supports a stronger claim.

## 5. Geographic resolution and accuracy

FloodGuard is initially focused on ward-level analysis.

### Limitations

- A ward-level score does not mean every location within that ward has the same risk.
- Ward-level exposure statistics cannot independently identify a flooded street, building, or household.
- Map accuracy depends on the quality and compatibility of ward boundaries and other geographic datasets.
- A reported coordinate may be inaccurate or may not precisely identify the affected area.
- Ward boundaries, infrastructure, drainage conditions, and other local characteristics may change over time.

### Mitigation

- Match ward identifiers to verified geographic boundaries.
- Investigate unmatched records rather than silently assigning them.
- Label the geographic level represented by each result.
- Do not imply street-level precision when only ward-level information is available.
- Clearly identify the source and limitations of any finer-grained geographic layer.

## 6. Citizen-submitted incident reports

Citizen reports may help surface potentially affected locations and provide additional context.

### Limitations

- Submitted reports are not automatically verified.
- Reports may be duplicated, inaccurate, misleading, or outdated.
- The number of reports may reflect reporting activity rather than the true severity or extent of flooding.
- A lack of reports does not prove that an area is safe.
- Simulated reports do not represent confirmed real-world incidents.

### Mitigation

- Distinguish submitted, unverified, and verified reports where these workflow states are implemented.
- Record submission timestamps and preserve verification status.
- Label simulated reports visibly in the interface.
- Avoid treating report volume alone as proof of flood severity.
- Define a documented method for handling duplicates and incorporating reports into the risk engine.
- Do not describe a report as verified unless the verification process has actually occurred.

## 7. Missing, unavailable, or stale data

Environmental information may be missing, delayed, inaccessible, or older than intended.

### Limitations

- A missing rainfall measurement does not mean that no rain occurred.
- A failed data request does not establish that conditions are safe.
- Stale information may no longer represent current conditions.
- A risk score calculated without important inputs may be less informative than a score based on complete, current data.

### Mitigation

FloodGuard should distinguish the following states where applicable:

- **Available:** The required input is present.
- **Unavailable:** The input could not be retrieved or is absent.
- **Stale:** The input exceeds its defined freshness threshold.
- **Simulated:** The input was generated for testing or demonstration.

The implementation must define suitable freshness thresholds for each source.

Missing or stale inputs must not be silently converted to zero values or automatically interpreted as low risk. Where critical information is unavailable, the application should communicate that limitation and avoid implying that the resulting assessment is fully informed.

Historical exposure information may still be displayed when current environmental data is unavailable, provided that the two are clearly distinguished.

## 8. Emergency response and public safety

FloodGuard is a decision-support prototype, not an emergency-response authority.

### Limitations

- Risk assessments may be incomplete, delayed, or incorrect.
- The prototype does not guarantee the identification of every dangerous location.
- No evacuation route or location should be described as safe without appropriate supporting data and validation.
- The availability of a risk assessment does not guarantee that emergency services have received or acted on the information.

### Mitigation

- Do not present FloodGuard as a replacement for official warnings, emergency services, or local authorities.
- Do not promise guaranteed protection, safe passage, or accurate flood prediction.
- Direct users to relevant official sources and emergency services for urgent situations.
- Make the prototype's scope and limitations visible to users.
- Do not deploy the system for consequential emergency decisions without appropriate validation, operational safeguards, and review.

## 9. Privacy and security

Citizen reports and application infrastructure must be designed to minimise unnecessary data exposure.

### Limitations

- User-submitted descriptions or location information may reveal sensitive personal details.
- Publicly exposed reports may create privacy or misuse risks.
- An operational prototype may not yet have all the authentication, authorisation, monitoring, and abuse-prevention controls required for public deployment.

### Mitigation

- Collect only information necessary for the intended feature.
- Avoid requesting unnecessary personal identifiers.
- Do not expose secrets, credentials, or unrestricted administrative operations.
- Apply appropriate access controls to report-management operations.
- Validate submitted data and handle errors safely.
- Review data retention, access, and deletion requirements before collecting real user data.
- Do not claim production-grade security until the relevant controls have been implemented and tested.

## 10. Prototype and infrastructure limitations

FloodGuard is being developed within a time-limited hackathon.

### Limitations

- Some features may remain incomplete or operate only with sample data.
- External data providers may impose access, reliability, or usage restrictions.
- AWS service configuration and application availability may vary during development.
- A successful demonstration does not prove that the application can support continuous operation or large-scale traffic.
- The use of AWS infrastructure does not, by itself, establish the scientific accuracy of the risk assessment.

### Mitigation

- Maintain a clear distinction between implemented, tested, planned, and simulated functionality.
- Test the integrated application rather than relying only on independently working components.
- Document external dependencies and known failures.
- Avoid claiming production readiness, guaranteed availability, or scalability without appropriate testing.
- Ensure that the demo reflects the actual application and does not imply that unimplemented features are operational.

## 11. Demonstration and communication rules

The presentation, application interface, documentation, and YouTube demo must communicate consistent and evidence-based claims.

The team must:

- Identify historical exposure data as historical.
- Distinguish observations, forecasts, historical records, and citizen reports.
- Label simulated data and outputs clearly.
- Explain that the initial risk method is heuristic rather than a validated predictive model.
- Avoid unsupported accuracy, impact, coverage, and performance claims.
- Avoid presenting planned features as completed features.
- Ensure that narration and visual overlays do not imply capabilities absent from the application.

AI-generated narration is a presentation method and does not establish the accuracy or validity of the underlying information.

## 12. Claims and evidence

The following table establishes the intended boundaries for project claims.

| Topic | Supported description | Claim to avoid without further evidence |
|---|---|---|
| Ward exposure | Historical estimate of potentially exposed population | Current number of people in danger |
| Risk score | Explainable heuristic assessment based on available inputs | Validated probability of flooding |
| Rainfall | Observation or forecast, according to the actual source | Live rainfall monitoring before integration is verified |
| Citizen reports | Submitted or verified reports, according to their actual status | Every report represents a confirmed flood |
| Geographic analysis | Ward-level assessment where ward-level data is used | Exact street-level flood prediction |
| Prediction accuracy | Method and evaluation results actually demonstrated | Unsupported accuracy percentages |
| AWS infrastructure | AWS services actually implemented and tested | Production readiness based solely on AWS usage |
| Environmental impact | Intended use and evidence-backed results | Quantified lives saved or losses prevented without evidence |

## 13. Limitations review checklist

Before a major demo or release, review the following:

- [ ] Verify the historical exposure figures against the original report.
- [ ] Confirm that historical data is labelled correctly in the interface.
- [ ] Confirm the actual status of every environmental data integration.
- [ ] Ensure observations and forecasts are distinguishable.
- [ ] Ensure simulated data and outputs are visibly labelled.
- [ ] Check that missing or stale data cannot silently produce a misleading low-risk result.
- [ ] Confirm that risk scores are explained and are not presented as calibrated probabilities.
- [ ] Check the geographic precision claimed by map features.
- [ ] Confirm that citizen-report verification states are accurate.
- [ ] Review privacy and access controls for implemented report workflows.
- [ ] Ensure the YouTube demo makes only claims supported by the working application.
- [ ] Update this document when significant capabilities or limitations change.

## 14. Final principle

FloodGuard aims to make flood-related information more understandable and useful by combining documented historical exposure with suitable environmental signals and incident reports.

Its value depends not only on the information it presents, but also on how clearly it communicates the reliability, freshness, geographic scope, and uncertainty of that information.

**FloodGuard must communicate what its data and tested features actually support, not what the team hopes they will eventually support.**