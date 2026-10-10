# FloodGuard System Architecture

**Project:** FloodGuard — Mumbai Hyperlocal Flood Intelligence  
**Status:** Working prototype; not production-ready  
**Version:** 1.2

## 1. Purpose

FloodGuard combines historical ward-level exposure context, available weather-model data, geographic context, and citizen incident reports to support an explainable, qualified view of flood and waterlogging concerns.

This document distinguishes the current deployed slice from work that remains planned. See [Prototype status](PROTOTYPE_STATUS.md) for the verification checkpoint and known gaps.

## 2. Current deployed architecture

```text
React / Vite frontend
       |
       | HTTPS / JSON
       v
Amazon API Gateway HTTP API
       |
       v
AWS Lambda (Python / FastAPI via adapter)
   |                  |
   v                  v
DynamoDB reports    Private S3 photo bucket
                        ^
                        |
             Browser uploads directly using
             a short-lived presigned POST

Lambda also calls the weather-model adapter and serves
the ward reference data and risk assessment.
CloudWatch provides AWS runtime logs.
```

The deployed resources verified for the current prototype include:
- API Gateway HTTP API in `ap-south-1`.
- Lambda function `floodguard-api`.
- DynamoDB table `floodguard-reports`.
- Private S3 bucket for report photo objects, with public access blocked.
- API CORS and S3 CORS configured for the local development origin used during testing.

Resource names are operational configuration, not secrets. Do not commit credentials, temporary URLs, or local environment files.

## 3. Verified end-to-end photo-report path

1. The frontend calls `POST /reports/photo-upload`.
2. Lambda creates a short-lived presigned S3 POST and stores a pending-upload record in DynamoDB.
3. The browser posts the image directly to S3. The upload contract limits accepted types to JPEG, PNG, and WebP and size to 5 MiB.
4. The frontend submits `POST /reports` with the upload ID.
5. The backend checks the pending record and expiry, checks S3 object metadata/size/type and image signature, and links the photo metadata to the persisted report.
6. The pending upload is marked consumed after report persistence.

This path was exercised successfully against the deployment. It does not imply every error path or security scenario has been tested.

## 4. Component responsibilities

### 4.1 Frontend — React, TypeScript, Vite

The frontend displays ward context, risk information, and report workflow. It supports an optional photo in the citizen report form. Mock mode exists for development; a demo using deployed data must explicitly use non-mock configuration.

### 4.2 API — FastAPI on Lambda

The backend validates input, serves reference/environmental/risk endpoints, and persists reports. It creates presigned upload forms and validates completed objects before associating them with reports.

The public citizen-report workflow and responder workflow have different access needs. The current responder dashboard has no sign-in, and backend responder authorization is not yet implemented.

### 4.3 Historical data and risk engine

Historical ward exposure is background vulnerability context. Open-Meteo supplies weather-model forecast data, not direct rain-gauge observations. Risk scores are rule-based prototype indices, not calibrated probabilities or official warnings. One representative weather point must not be presented as independent weather data for every ward.

### 4.4 DynamoDB and S3

DynamoDB stores report records and internal pending photo-upload records. Internal upload records use a separate key prefix and are filtered from normal report listings.

S3 stores uploaded photo objects privately. Browser upload is authorized with a short-lived presigned POST. The application must not make the bucket public or expose AWS credentials.

## 5. Security boundary and next architecture milestone

**Not implemented yet:** responder sign-in, backend responder role authorization, and secure responder photo retrieval.

The responder UI's prototype status message is not an access-control mechanism. A future implementation should use an identity provider such as Amazon Cognito, validate the access token on the backend, and authorize responder-only operations server-side.

Planned protected flow:

```text
Responder signs in
       |
       v
Frontend obtains access token
       |
       v
API validates token and responder role
       |
       +--> authorized report status update
       |
       +--> GET /reports/{report_id}/photo-url
                    |
                    v
          verify report/photo association
                    |
                    v
          short-lived presigned S3 GET
```

The photo URL endpoint must return a URL only after authentication/authorization and confirming that the requested report has an available associated photo. The URL is a bearer credential until it expires, so its lifetime should be short and it must not be logged or persisted by the frontend.

## 6. Not part of the current verified slice

- Cognito responder authentication and backend authorization.
- Responder-only presigned photo downloads.
- Production monitoring/alerting and operational readiness.
- Claims of calibrated flood prediction or official warning capability.

Do not describe these items as deployed until implementation and verification are complete.
