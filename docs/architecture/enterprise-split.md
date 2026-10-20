<!-- RFC: Enterprise Frontend/Backend Split Deployment -->

# Enterprise Frontend/Backend Split Deployment RFC

## 1. Executive Summary

Enterprise tenants require stricter isolation, change control, and performance guarantees than the shared Pro stack can offer. This RFC proposes decoupling the current monolith into independently deployable frontend and backend packages with hardened network boundaries, regional scaling, and dedicated CI/CD.

## 2. Current Constraints

- **Single runtime**: React + FastAPI are served from the same origin, limiting WAF / CDN optimizations.
- **Shared databases**: Enterprise data sits beside Pro tenants despite organization-level RBAC.
- **Release coupling**: UI hotfixes require backend redeploys, increasing change risk.
- **Compliance**: FedRAMP-style logging and key rotation are harder when infra is shared.

## 3. Target Architecture

| Layer              | Proposed Change                                             |
|--------------------|-------------------------------------------------------------|
| Frontend           | Static React bundle deployed to regional CDN (CloudFront) with Web Application Firewall rules dedicated to enterprise tenants. |
| Backend            | FastAPI container hosted on isolated Kubernetes namespace (EKS) with service mesh (App Mesh) to enforce zero-trust policies. |
| Data               | Separate PostgreSQL cluster per region with read replicas for analytics; encrypted S3 bucket for file storage. |
| Networking         | Private API Gateway + VPC link; OAuth/OpenID broker to support customer IdPs. |

### Service Boundaries
1. **Identity**: Shared Auth0 tenant with enterprise-specific connections.
2. **Notifications**: SNS topics per tenant; workers subscribe from isolated queues.
3. **Storage**: Dedicated S3 prefixes mounted via presigned URLs; backend never exposes raw paths.

## 4. Deployment Plan

### Phase 0 – Foundations (Week 1)
- Create new IaC modules (Terraform) for enterprise VPC, EKS namespace, and RDS cluster.
- Enable feature flag `enterprise_split` in backend settings.

### Phase 1 – Backend Extraction (Weeks 2-3)
- Containerize FastAPI as `enterprise-api` image.
- Implement Envoy gateway for auth + rate limiting.
- Configure Alembic migrations to target enterprise database using new DSN.

### Phase 2 – Frontend Static Hosting (Week 4)
- Build React bundle with `VITE_API_BASE_URL=https://enterprise-api.company.com`.
- Deploy to CloudFront with signed URLs; enable cache invalidation workflow.

### Phase 3 – Traffic Cutover (Week 5)
- Mirror production traffic via dual-write (shared + enterprise stack) for smoke testing.
- Flip DNS for enterprise subdomain once health checks are green.

### Phase 4 – Decommission Legacy Paths (Week 6)
- Remove enterprise feature flags from shared stack.
- Archive shared tenant data snapshots per compliance policy.

## 5. Operational Controls

- **Monitoring**: Dedicated Prometheus + Grafana dashboards; SLOs on p95 latency & error budgets.
- **Logging**: Ship audit + access logs to tenant-specific CloudWatch log groups with 1-year retention.
- **Key Management**: KMS CMKs per tenant for database + S3 encryption.
- **Disaster Recovery**: Automated cross-region snapshots nightly; failover runbooks documented in runbook repo.

## 6. Open Questions

1. Should we co-locate AI workloads with enterprise backend to avoid egress?
2. Do we need customer-managed keys (CMK BYOK) for regulated sectors?

## 7. Next Steps

- Approve budget for additional AWS accounts.
- Convert this RFC into tracked epic with sub-tasks for IaC, CI/CD, and migration tooling.
- Schedule customer communication regarding maintenance windows.

