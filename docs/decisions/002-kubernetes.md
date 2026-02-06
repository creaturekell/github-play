# Design Decision: Kubernetes for Preview Environments

Date: 2026-02-04  
Status: Accepted

## Context

Preview environments are ephemeral by nature: they are created on demand, serve live traffic for a short period of time, and must be reliably cleaned up to avoid unnecessary cost.

In this system, preview environments must support:
- Many concurrent deployments (e.g., dozens of PRs at once)
- Independent isolation between previews
- Automatic expiration and cleanup
- Repeatable, predictable provisioning
- A clear path to production parity

The preview deploy service is responsible for creating, exposing, and tearing down these environments safely and efficiently.

## Alternatives Considered

### Option 1: VM-based or Static Environments

A VM-based approach or a fixed pool of preview environments was considered.

Drawbacks:
- Slow provisioning times
- Poor density and resource utilization
- Manual or brittle cleanup logic
- Harder to scale dynamically with PR volume
- Less alignment with modern production deployment models

This approach increases operational overhead and limits scalability.

### Option 2: Platform-as-a-Service (PaaS)

A managed PaaS could simplify deployment and infrastructure management.

Drawbacks:
- Limited control over environment lifecycle
- Difficult to enforce strict TTL-based cleanup
- Less flexibility for custom routing, isolation, and observability
- Reduced parity with production environments

While appealing for simplicity, this option constrains long-term extensibility.

## Decision

Use **Kubernetes** as the underlying platform for managing preview environments.

Each preview deployment is provisioned as an isolated Kubernetes namespace containing:
- Application deployment
- Service
- Ingress configuration
- Associated metadata for ownership and TTL

Namespaces are created on demand and deleted automatically when the preview expires.

## Rationale

Kubernetes provides several key advantages for this use case:

1. **Strong Isolation Boundaries**  
   Namespaces provide a natural and enforceable isolation model between preview environments, reducing blast radius and simplifying cleanup.

2. **Scalability and Resource Efficiency**  
   Kubernetes efficiently schedules containers across shared infrastructure, allowing many preview environments to coexist without dedicated machines per PR.

3. **Declarative Infrastructure**  
   Kubernetes manifests make preview environments reproducible, auditable, and easier to reason about compared to imperative deployment scripts.

4. **Lifecycle Management**  
   Kubernetes APIs make it straightforward to create, monitor, and delete resources programmatically, which aligns well with TTL-based preview cleanup.

5. **Production Parity**  
   Using the same orchestration platform for previews and production reduces configuration drift and increases confidence that previews accurately reflect production behavior.

6. **Extensibility**  
   Kubernetes enables future enhancements such as:
   - Resource quotas per preview
   - Network policies
   - Autoscaling
   - Integrated observability and tracing
   - Policy enforcement

## Consequences

### Positive
- Supports high concurrency of preview environments
- Predictable and repeatable deployments
- Strong isolation and cleanup guarantees
- Better alignment with production deployment patterns
- Enables future scaling and governance capabilities

### Negative
- Increased operational complexity
- Requires Kubernetes cluster management
- Higher initial learning and setup cost compared to simpler platforms

These tradeoffs are acceptable given the scalability, safety, and extensibility benefits for this system.

