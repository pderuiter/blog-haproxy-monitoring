# blog-haproxy-monitoring

Companion code for the blog post
[HAProxy Monitoring with Prometheus: Complete Observability Guide](https://blog.bsdserver.nl/haproxy-monitoring-with-prometheus-complete-observability-guide/).

It builds the post's setup: HAProxy from the official repositories with the built-in Prometheus
exporter on `:8405/metrics`, a stats page on `:8404/stats`, and the `http_front` /
`web_servers` application frontend and backend; plus a Prometheus server that scrapes every
HAProxy host and loads the post's alerting rules (`haproxy_alerts.yml`) and recording rules
(`haproxy_rules.yml`) unchanged. The post's Grafana dashboard is in `grafana/` for import.

## What is in here

| Path | Purpose |
|------|---------|
| `terraform/` | Two Ubuntu 24.04 VMs on Proxmox VE (bpg/proxmox provider, cloud-init), outputs an Ansible inventory |
| `ansible/site.yml` | One playbook for the whole setup |
| `ansible/roles/haproxy_install` | HAProxy from the vbernat PPA (Ubuntu) or haproxy.debian.net (Debian), via `deb822_repository` |
| `ansible/roles/haproxy_metrics` | The post's `haproxy.cfg`: exporter frontend, stats page, application frontend/backend |
| `ansible/roles/prometheus` | Prometheus from the official release tarball, systemd unit, `prometheus.yml`, the post's rules |
| `ansible/roles/demo_backend` | **Demo only**: two tiny HTTP servers that stand in for the post's web servers |
| `grafana/haproxy-overview.json` | The post's "HAProxy Overview" dashboard (Grafana itself is not installed) |

Not included: the separate `haproxy_exporter` from the post's "HAProxy Exporter (Alternative)"
section. That project is archived upstream (last release 0.15.0) and the native exporter
replaces it, which is what the rest of the post and this repo use.

## Requirements

- Terraform >= 1.6 and a Proxmox VE API token (only if you want Terraform to create the VMs)
- ansible-core >= 2.15 (tested with 2.20)
- Target hosts: Ubuntu 24.04 (tested). Debian 13 is handled by `haproxy_install` but not lab-tested here.

## Quick start

```bash
# 1. Machines (optional; skip if you already have two hosts)
cd terraform
cp terraform.tfvars.example terraform.tfvars   # fill in your values
terraform init
terraform apply
terraform output -raw ansible_inventory > ../ansible/inventory.yml

# 2. HAProxy and Prometheus
cd ../ansible
cp inventory.example.yml inventory.yml         # if you skipped Terraform
ansible-playbook site.yml

# 3. Test (sections "Verify Metrics Endpoint" and "Troubleshooting" of the post)
curl http://10.0.0.10:8405/metrics | grep haproxy_process_nbthread
curl -s http://10.0.0.20:9090/api/v1/targets | jq '.data.activeTargets[] | select(.job=="haproxy") | .health'
curl -s http://10.0.0.20:9090/api/v1/rules | jq '.data.groups[].name'
```

Hosts in the `haproxy` group get HAProxy; hosts in the `prometheus` group get Prometheus,
which scrapes every `haproxy` host on port 8405.

## Variables

Set in `ansible/group_vars/all/vars.yml` (defaults in each role's `defaults/main.yml`):

| Variable | Default | Meaning |
|----------|---------|---------|
| `haproxy_install_version` | `3.3` | HAProxy branch. 3.3 is the newest the PPA builds for Ubuntu 24.04 (maintained to about Q1 2027); `3.2` is LTS on 24.04, `3.4` LTS on Ubuntu 26.04 / Debian 13 |
| `haproxy_metrics_backend_servers` | post: web1..web3 on `192.168.1.10-12:8080`; group_vars: the demo backends | Servers of `web_servers` (name, address, port) |
| `haproxy_metrics_tls` | `true` | Bind `:443` with every certificate in `/etc/haproxy/certs/`; a self-signed one is generated if there is none |
| `demo_backend_enabled` | `true` (group_vars) | Run the demo HTTP servers on 127.0.0.1:8081/8082. Set `false` for real web servers |
| `prometheus_version` | `3.16.0` | Prometheus release; changing it installs the new release next to the old one and restarts |
| `prometheus_alertmanagers` | `["alertmanager:9093"]` | As in the post. No Alertmanager is installed; set yours, or `[]` |
| `prometheus_haproxy_group` / `prometheus_haproxy_port` | `haproxy` / `8405` | Which hosts are scraped |
| `prometheus_haproxy_extra_targets` | `[]` | More HAProxy targets (`host:port`) outside the inventory |

The alerting and recording rules are in `ansible/roles/prometheus/files/` exactly as in the
post; Ansible validates them with `promtool check rules` and `prometheus.yml` with
`promtool check config --syntax-only` before installing.

This setup has no secrets, so `group_vars/all/vault.yml.example` is empty. Note that the
metrics and stats frontends are open to anyone who can reach them, as in the post; restrict
them with a firewall or an ACL in production.

## Terraform variables

See `terraform/variables.tf` and `terraform/terraform.tfvars.example`. The VMs are defined in
the `vms` map (name, IP in CIDR notation, Ansible groups, optional cores/memory/disk).

## Tested

`site.yml` was run against fresh Ubuntu 24.04 systemd containers (HAProxy 3.3.17,
Prometheus 3.16.0). The second run, and a run after restarting both services, report
`changed=0`. Afterwards: HTTP and HTTPS through `http_front` return 200, `/metrics` serves
the `haproxy_*` metrics with both demo servers `UP`, the Prometheus `haproxy` target is up,
both rule groups (10 alerts, 5 recording rules) are loaded and healthy, and the recording
rules and `haproxy_frontend_http_requests_total` queries return data. ansible-lint
(production profile), yamllint, `terraform validate` and tflint are clean. The Terraform code
has not been applied against a real Proxmox cluster.

## License

MIT
