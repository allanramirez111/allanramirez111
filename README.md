<h1 align="center">Allan Santiago Ramírez Mateus</h1>

<p align="center">
  <b>Risk engineer</b> · I build the software that regulated financial institutions use to
  measure interest-rate, liquidity, operational and credit risk.<br>
  Statistician (UNAL) · MSc Analytics (Uniandes) · Bogotá, Colombia
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white">
  <img src="https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black">
  <img src="https://img.shields.io/badge/Go-00ADD8?style=flat-square&logo=go&logoColor=white">
  <img src="https://img.shields.io/badge/Terraform-7B42BC?style=flat-square&logo=terraform&logoColor=white">
  <img src="https://img.shields.io/badge/AWS-232F3E?style=flat-square&logo=amazonwebservices&logoColor=white">
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white">
  <img src="https://img.shields.io/badge/R-276DC3?style=flat-square&logo=r&logoColor=white">
</p>

<p align="center">
  <a href="https://www.linkedin.com/in/allan-santiago-ramirez-mateus/"><img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=flat-square&logo=linkedin&logoColor=white"></a>
  <a href="mailto:ramaasa@gmail.com"><img src="https://img.shields.io/badge/Email-EA4335?style=flat-square&logo=gmail&logoColor=white"></a>
</p>

---

<!--METRICS:start-->
### Activity

**5,878** contributions in the last year &nbsp;·&nbsp; **108** active days &nbsp;·&nbsp; **4,452** commits authored across **25** repositories

```text
Python         █████████████████▊            63.3%
TypeScript     █████▍                        19.3%
R              ███▌                          12.6%
Go             ▋                              2.4%
HCL            ▍                              1.1%
Shell          ▏                              0.7%
```

<sub>Language split by source bytes; notebooks and generated HTML excluded. Most of the work lives in private product repositories; these numbers come from the GitHub API, not from a hand-written list. Updated 2026-09-06.</sub>
<!--METRICS:end-->

---

## What I'm building

Risk software for regulated financial institutions — Basel/EBA on the banking side,
Supersolidaria on the co-op side. The code is in private product repos, so this page
describes what it is and how it is built rather than linking to it.

| | What it does | Stack |
|---|---|---|
| **ALM / IRRBB engine** | Interest-rate risk in the banking book: NIIF 9 contractual cash flows, EVE/VEP and NII indicators per **BCBS 368** and **EBA GL 2018/02**, plus reference LCR/NSFR. French amortization, monthly CPR, 19 time buckets, multi-currency. Ships two ways from one codebase: single-tenant on-premise via Docker, and multi-tenant SaaS. | Python 3.11 · React/TS · Terraform · AWS ECS Fargate · RDS · ElastiCache |
| **SARO** — operational risk | Risk taxonomy parameterized by regulatory framework (CO-SES per Supersolidaria's CBCF, CO-SFC per Basel/SFC), inherent/residual scoring, control registry, heat maps. In pilot on staging with a financial institution. | Python · FastAPI · PostgreSQL · Terraform · AWS |
| **Institutional performance eval.** | Scoring engine plus a React console over weighted indicators, bands and instruments. | Python · TypeScript/React · Terraform · AWS |
| **Credit-risk indicator suite** | Vintage/cohort analysis, transition matrices and reserve models (roll-rate, charge-off, payment factors, P&L impact) on a serverless pipeline. | Python · DuckDB · AWS Lambda · Step Functions · LocalStack |
| **Design system** | Brand tokens vendored into each product, pinned by source SHA in a `VENDOR.txt` manifest; a guard test re-hashes every vendored file and fails CI on a single changed byte. | CSS · Python |

*Specced, not yet built* — liquidity risk engine (IRL, standard Supersolidaria methodology,
early-warning triggers, stress scenarios) and risk appetite (four-zone classification,
financial-statement projection, SIAR indicators): ~170 KB of functional spec written,
implementation queued.

---

## How I work

**Tests and CI are not optional.** 967 test files across the product codebases — 560 of
them in the ALM engine alone. CI runs on push, with Terraform `fmt`/`validate` as its own
job. Infrastructure is Terraform, not click-ops.

**A vendored asset without verification is worse than a CDN — the CDN at least updates.**
Every vendored file carries its sha256 in a manifest and its origin SHA in its own header;
a test compares all three and names the offending file.

**I verify instead of assuming.** The Postgres restore runbook was rehearsed against
staging: RTO 70 min end to end, RPO measured at 6 min 55 s against a spec that promised
5 min. The promise was rewritten, not the measurement.

**I write down the trade-offs that don't flatter me.** Moving CI to a self-hosted runner
cut per-job time (2m22s → 1m21s) but raised wall-clock per PR (2m22s → 2m49s), because the
jobs stopped running in parallel. That is in the ADR, including what it costs.

Happy to walk through the architecture, the CI setup or the test strategy in a call — I
just can't open the repos.

---

## Background

- **Credit risk analytics** — vintage/cohort analysis, transition matrices, reserve models.
- **Data pipelines** — SQL-first (PostgreSQL, DuckDB); ETL that other people can debug.
- **Interpretability first** — models should be explainable, pipelines observable, decisions traceable.

<p align="center"><sub>Open to conversations about risk engineering, regulated fintech products, and Python/Go backends.</sub></p>
