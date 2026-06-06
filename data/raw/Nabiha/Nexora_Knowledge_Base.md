# Nexora Cloud Knowledge Base

## KB-1001: Account Login Guide
Category: Account Management

### Overview
This article explains how users can sign in to their Nexora Cloud account.

### Steps
1. Open the Nexora Cloud login page.
2. Enter your registered email address.
3. Enter your password.
4. Click Sign In.
5. Complete MFA verification if enabled.

### Common Issues
- Invalid credentials → Verify email and password.
- Account locked → Wait 15 minutes or contact support.
- MFA code not accepted → Sync device time and retry.

---

## KB-1002: Password Reset Flow
Category: Account Management

### Steps
1. Click Forgot Password.
2. Enter your registered email.
3. Select Send Reset Link.
4. Open the email and click the reset link.
5. Create a new password.
6. Sign in using the new password.

### Password Requirements
- Minimum 12 characters
- One uppercase letter
- One number
- One special character

---

## KB-1003: MFA Troubleshooting
Category: Security

### Common Problems
- Authenticator code fails
- Lost authentication device
- SMS code not received

### Resolution
- Enable automatic time sync.
- Use backup recovery codes.
- Contact support if recovery methods are unavailable.

---

## KB-2001: Billing and Refund Policy

### Refund Eligibility
- Duplicate charge: Eligible
- Service outage exceeding SLA: Eligible
- User cancellation after renewal: Not eligible
- Trial period cancellation: Eligible

---

## KB-3001: API Usage Documentation

### Authentication
Use API keys generated from the Developer Portal.

### Example Request
GET /v1/projects
Authorization: Bearer API_KEY

### Rate Limits
- Starter: 100 RPM
- Professional: 500 RPM
- Enterprise: 2000 RPM

---

## KB-4001: Escalation Procedure

### Severity Levels
- P1: Complete service outage
- P2: Major feature unavailable
- P3: Partial degradation
- P4: General inquiry

---

## KB-5001: System Outage Handling

### Response Workflow
1. Incident declared
2. Incident commander assigned
3. Engineering investigation begins
4. Customer communication published
5. Service restored
6. Postmortem completed

---

## KB-6001: Customer Onboarding Guide

### Initial Setup Checklist
- Create account
- Verify email
- Enable MFA
- Configure billing
- Create first project
- Add team members
