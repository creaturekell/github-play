# NGINX Ingress Quick Start Guide

## Prerequisites

- Kubernetes cluster (GKE) with `kubectl` configured
- A Google Cloud static IP (recommended) for previews
- Wildcard DNS record `*.yourhostname.com` pointing to that IP
- Preview Helm chart in this repo (`helm-chart/`)

## 1. Deploy NGINX Ingress Controller

From the repo root:

```bash
cd helm-chart
kubectl apply -f nginx/nginx-ingress.yaml
```

Wait for the controller Service to get an external IP:

```bash
kubectl get svc -n ingress-nginx ingress-nginx-controller
```

Note the `EXTERNAL-IP` value.

## 2. Point Wildcard DNS to NGINX

Update your wildcard DNS (e.g. in Google Cloud DNS or Namecheap) so:

- `*.yourhostname` → `EXTERNAL-IP` of `ingress-nginx-controller`

Once DNS propagates, any `*.hostname` hostname will reach the NGINX ingress controller.

## 3. Deploy a Preview Environment

Update `values-preview.yaml` for the specific PR:

- `ingress.hosts[0].host`: set to the preview hostname, e.g.:

  ```yaml
  ingress:
    enabled: true
    className: "nginx"
    hosts:
      - host: preview-pr-123.yourhostname
        paths:
          - path: /
            pathType: Prefix
  ```

Deploy with Helm:

```bash
cd helm-chart

helm install preview-pr-123 . \
  --namespace preview-pr-123 \
  --create-namespace \
  -f values-preview.yaml
```

This creates:

- A `Deployment` running the preview app
- A `Service` exposing port 8080
- An `Ingress` with `ingressClassName: nginx` pointing `preview-pr-123.yourhostname` to that Service

## 4. Verify the Preview

Check Kubernetes resources:

```bash
kubectl get pods,svc,ingress -n preview-pr-123
```

Then test from your browser:

- Open `https://preview-pr-123.yourhostname` (or `http://` if you haven’t added TLS yet)

If you want to test from inside the cluster:

```bash
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl -v http://preview-pr-123-preview-environment.preview-pr-123.svc.cluster.local:8080/
```

## 5. Cleanup

Remove a specific preview:

```bash
helm uninstall preview-pr-123 -n preview-pr-123
kubectl delete namespace preview-pr-123
```

Optionally remove NGINX ingress:

```bash
kubectl delete -f nginx/nginx-ingress.yaml
```

## 6. Troubleshooting: URL Not Accessible

If the preview URL does not work after deployment, run these checks:

### Step 1: Verify Ingress exists

```bash
kubectl get ingress -n preview-pr-123
```

You should see `preview-pr-123-preview-environment` with `CLASS: nginx`. If missing, run `helm upgrade` with the correct values.

### Step 2: Get NGINX external IP

```bash
kubectl get svc -n ingress-nginx ingress-nginx-controller
```

- If `EXTERNAL-IP` is `<pending>`, wait 1–5 minutes for GKE to provision the LoadBalancer.
- Note the `EXTERNAL-IP` value (e.g. `34.123.45.67`).

### Step 3: Verify DNS points to NGINX

```bash
dig +short preview-pr-123.yourhostname
```

The result **must** match the NGINX `EXTERNAL-IP`. If it resolves to a different IP (e.g. an old GCE ingress), update your wildcard DNS:

- In Google Cloud DNS: `*.yourhostname` A record → NGINX IP
- In your domain register Custom DNS or host records → NGINX IP

### Step 4: Test backend from inside cluster

```bash
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n preview-pr-123 -- \
  curl -s http://preview-pr-123-preview-environment:8080/
```

---

## 7. Notes

- NGINX ingress controller watches standard Kubernetes `Ingress` objects with `ingressClassName: nginx`.
- All previews share the same external IP and wildcard DNS; each preview is a separate namespace + Service + Ingress.
- Time to first URL is typically:
  - Pod scheduling + image pull: ~10–30s
  - Ingress creation and discovery by NGINX: a few seconds

