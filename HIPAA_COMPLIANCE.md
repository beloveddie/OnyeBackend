# HIPAA Compliance & Secure FHIR Data Handling

## Technical Implementation Strategy

### 1. Authentication & Authorization Mechanisms

#### OAuth 2.0 with SMART on FHIR
Implement **SMART on FHIR** (Substitutable Medical Applications, Reusable Technologies) as the primary authorization framework:

- **Authorization Server**: Deploy OAuth 2.0-compliant authorization server supporting SMART App Launch Framework
- **Token Types**: 
  - Access tokens (JWT) with 15-minute expiration
  - Refresh tokens (30-day expiration) stored securely with encryption at rest
- **Scopes**: Implement granular FHIR resource scopes (e.g., `patient/Patient.read`, `user/Observation.*`, `system/Condition.read`)
- **PKCE**: Require Proof Key for Code Exchange for all public clients to prevent authorization code interception

**Implementation Example**:
```python
# FastAPI dependency for token validation
from fastapi.security import OAuth2AuthorizationCodeBearer
from jose import jwt, JWTError

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://auth.example.com/authorize",
    tokenUrl="https://auth.example.com/token"
)

async def validate_token(token: str = Depends(oauth2_scheme)):
    # Verify JWT signature, expiration, and scopes
    # Extract user context and patient context from token
    return validated_user_context
```

#### Multi-Factor Authentication (MFA)
- Mandatory MFA for healthcare providers accessing PHI
- Support TOTP, SMS, and biometric authentication methods
- Session management with secure, httpOnly cookies

---

### 2. Data Privacy & Audit Logging Strategy

#### Data Encryption
- **In Transit**: Enforce TLS 1.3 for all API communications; reject TLS 1.2 and below
- **At Rest**: AES-256 encryption for all PHI in databases and file systems
- **Field-Level Encryption**: Encrypt sensitive fields (SSN, medical record numbers) with separate encryption keys managed via AWS KMS or Azure Key Vault

#### Data Minimization
- Return only requested FHIR resources based on OAuth scopes
- Implement field-level filtering to exclude unnecessary PHI elements
- Use de-identification algorithms for analytics and research queries

#### Comprehensive Audit Logging
Implement **FHIR AuditEvent** resources compliant with HIPAA's Access and Audit Controls (§164.312(b)):

**Log Structure**:
```json
{
  "resourceType": "AuditEvent",
  "type": {
    "system": "http://terminology.hl7.org/CodeSystem/audit-event-type",
    "code": "rest",
    "display": "RESTful Operation"
  },
  "action": "R",
  "recorded": "2025-10-12T14:30:00Z",
  "agent": [{
    "who": {"reference": "Practitioner/123"},
    "requestor": true,
    "network": {"address": "192.168.1.100", "type": "2"}
  }],
  "source": {"observer": {"reference": "Device/api-server-01"}},
  "entity": [{
    "what": {"reference": "Patient/456"},
    "type": {"system": "http://hl7.org/fhir/resource-types", "code": "Patient"}
  }]
}
```

**Audit Requirements**:
- Log all PHI access, modifications, and deletions with user identity, timestamp, IP address, and action type
- Immutable audit logs stored in append-only datastores (e.g., AWS CloudWatch Logs, Azure Monitor)
- Real-time anomaly detection for suspicious access patterns (e.g., bulk downloads, off-hours access)
- Retain audit logs for minimum 6 years per HIPAA requirements

---

### 3. Role-Based Access Control (RBAC)

#### RBAC Architecture
Implement hierarchical role structure aligned with healthcare workflows:

| Role | FHIR Scopes | Access Level | Use Case |
|------|-------------|--------------|----------|
| **Patient** | `patient/*.read` | Own records only | Patient portal access |
| **Nurse** | `user/Patient.read`, `user/Observation.*` | Assigned patients | Clinical documentation |
| **Physician** | `user/*.read`, `user/*.write` | Full clinical access | Diagnosis, prescriptions |
| **Admin** | `user/*.read`, `system/User.*` | Organization-wide | User management |
| **System** | `system/*.*` | Background processes | Data integration, backups |

#### Dynamic Context-Based Access Control
Extend RBAC with contextual attributes:
- **Patient Context**: Restrict access to patients under provider's care (relationship verification via CareTeam resources)
- **Break-the-Glass**: Emergency access override with mandatory justification and enhanced audit logging
- **Time-Based Access**: Restrict access outside normal working hours with alerts
- **Location-Based**: Geo-fencing for on-premises-only access to highly sensitive data

**Implementation**:
```python
def check_access(user: User, resource: FHIRResource, action: str) -> bool:
    # 1. Verify role permissions
    if not user.role.has_permission(resource.type, action):
        return False
    
    # 2. Check patient relationship (for patient-specific resources)
    if resource.subject:
        if not verify_care_relationship(user.id, resource.subject.id):
            return False
    
    # 3. Verify OAuth scopes from token
    required_scope = f"{user.scope_type}/{resource.type}.{action}"
    if required_scope not in user.token_scopes:
        return False
    
    # 4. Contextual checks (location, time, break-the-glass)
    if not validate_context(user, resource):
        return False
    
    return True
```

---

### 4. Additional HIPAA Safeguards

#### Technical Safeguards (§164.312)
- **Automatic Logoff**: 15-minute inactivity timeout for sessions
- **Encryption Key Management**: Rotate encryption keys quarterly; use HSMs for key storage
- **Integrity Controls**: Use digital signatures to detect unauthorized PHI modifications
- **Transmission Security**: Enforce mutual TLS for system-to-system communications

#### Administrative Safeguards (§164.308)
- **Security Training**: Quarterly HIPAA training for all engineers with access to production systems
- **Incident Response**: Documented breach notification procedures compliant with 72-hour reporting requirement
- **Business Associate Agreements**: Ensure all third-party services (hosting, monitoring) have signed BAAs

#### Physical Safeguards (§164.310)
- Host infrastructure in HIPAA-compliant cloud environments (AWS, Azure, Google Cloud with BAAs)
- Implement workstation security policies (encrypted devices, VPN-only access to production)

---

### 5. Monitoring & Compliance Validation

#### Continuous Monitoring
- **SIEM Integration**: Stream audit logs to Security Information and Event Management system
- **Automated Compliance Checks**: Daily scans for unencrypted data, weak access controls, expired credentials
- **Vulnerability Scanning**: Weekly automated penetration testing of API endpoints

#### Regular Audits
- Quarterly internal HIPAA risk assessments
- Annual third-party security audits (SOC 2 Type II, HITRUST)
- Monthly access reviews to revoke unnecessary permissions

---

## Implementation Roadmap

**Phase 1 (Weeks 1-2)**: OAuth 2.0 + SMART on FHIR implementation  
**Phase 2 (Weeks 3-4)**: Encryption at rest and in transit; audit logging infrastructure  
**Phase 3 (Weeks 5-6)**: RBAC engine with patient context verification  
**Phase 4 (Weeks 7-8)**: Monitoring, alerting, and compliance validation tools  

---

**Compliance Attestation**: This architecture ensures adherence to HIPAA Privacy Rule (45 CFR §164.502), Security Rule (45 CFR §164.306-318), and Breach Notification Rule (45 CFR §164.400-414), while maintaining interoperability through HL7 FHIR R4 standards.
