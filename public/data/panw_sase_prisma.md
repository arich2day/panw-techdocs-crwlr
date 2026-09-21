# [DOMAIN: SASE & SSE] [VENDOR: PALO ALTO NETWORKS] Prisma Access Architecture & Release Notes
- Target ID: panw_sase_prisma
- Generated: 2026-09-21 23:41:13 UTC
- Word Count: 118 words
- Source URLs: https://docs.paloaltonetworks.com/prisma/prisma-access/prisma-access-panorama-admin/prisma-access-overview/prisma-access-infrastructure, https://docs.paloaltonetworks.com/prisma/prisma-access/release-notes
---

### Enterprise Architecture & Strategic Overview
Prisma Access multi-tenant backbone, service connection topology, QoS, and release caveat advisories.

#### Core Architecture Principles
- **Domain**: SASE & SSE (SASE)
- **Vendor Alignment**: Palo Alto Networks (PRIMARY)
- **Zero Trust Tenet**: Explicit verification of identity, device posture, and continuous content inspection.
- **Telemetry & Logging**: Native integration with enterprise SIEM/SOAR (Cortex XSIAM, Splunk) and Cloud Data Lakes.

#### Technical Capabilities & Operational Caveats
- **Datapath Processing**: Single-pass parallel architecture eliminating proxy chaining latency.
- **High Availability & Redundancy**: Multi-region active-active deployment with automated route failover (BGP/IPsec).
- **Policy Lifecycle**: Centralized policy orchestration via Panorama, Strata Cloud Manager, or Terraform/pan.dev APIs.
- **Key Tags**: Prisma Access, Zero Trust, Cloud SWG, ZTNA
