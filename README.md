# CRE Expected Loss AI Agent

Independent local application for exploring AI orchestration, memory, governance, failure recovery, evaluation and estimated cost controls around CRE analytical tools.

Current scope: synthetic EAD demonstrations and an optional read-only comparison of locally supplied aggregate LGD research reports. Full expected-loss modeling is not implemented. Recorded agent decisions are scripted; the Gemini adapter is implemented but live generation remains unverified and disabled by policy. No production readiness, independent validation or institutional approval is claimed.

## Setup

Requires Python 3.11+ and the trusted [CRE Expected Loss repository](https://github.com/raji-ramachandran-tampa/cre_ead_pd_lgd), whose EAD function remains the authoritative calculation. Clone both repositories into adjacent directories, or set `CRE_REPO` to an absolute path to that trusted checkout.

```powershell
git clone https://github.com/raji-ramachandran-tampa/cre_ead_pd_lgd
git clone https://github.com/raji-ramachandran-tampa/cre-expected-loss-ai-agent
cd cre-expected-loss-ai-agent
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python server.py
```

Keep the server terminal running and open http://127.0.0.1:8765/. The service listens only on loopback. On macOS/Linux use `.venv/bin/python`. For a complete pinned dependency snapshot, install `requirements-lock.txt` instead.

## Demonstrate the capabilities

Start with **Governance**. Try permitted synthetic inputs, unregistered inputs, unapproved tools and agent approval authority. The same checker protects actual tool execution. Expand **Other agent capabilities and evidence** for memory, injected failure recovery, separate-process resume, orchestration, evaluation, observability and zero-budget stopping. The synthetic comparison needs no API key or paid requests.

Conversation history, working results and durable memories have separate responsibilities. Memories require provenance and expire from retrieval after at most 24 hours. SQLite checkpoints survive restart; stable call IDs cache completed outputs. Provider calls with ambiguous outcomes stop and retain a visible allowance instead of being blindly replayed. Local events explain decisions, tools, failures, latency and usage.

## Optional LGD comparison

No Fannie Mae datasets, loan records, local research metrics, prediction files, model binaries or screenshots of private results are included. The comparison expects authorized local JSON reports under `LGD_REPORT_ROOT`, with these relative paths:

- `lgd-signed-research-v0.1.0/report.json`
- `lgd-signed-hurdle-v0.1.1/report.json`

This compares ridge regression with loss-sharing features and a signed hurdle model using a shared signed source-loss ratio. It verifies the reported outcome version, case counts and finite metrics and records report hashes. It reads previously computed aggregates; it does not fit models or independently verify row pairing. A signed source-loss ratio is not discounted economic workout LGD. Without compatible local reports this optional action returns a file error; synthetic demonstrations still work.

Fannie Mae data access and use are governed by the applicable source terms. Keep data and derived artifacts local and out of Git. Local reports are never sent to an AI provider by this comparison tool.

## Governance and AI access

`governance-policy.json` versions the tool allowlist, synthetic case IDs, memory retention and live-provider gate. The local operator is responsible for policy changes. Live requests are disabled by default even when Gemini is selected. Enabling them requires deliberate operator authorization, a verified price configuration and `GEMINI_API_KEY` supplied through the environment. Never commit credentials.

The agent cannot approve a model, change source code or make lending decisions. There is no enterprise identity system, signed policy enforcement, immutable audit store or distributed execution. Memory expiration excludes retrieval; it does not physically purge historical logs and checkpoints. Cost controls govern configured estimates per run, not actual invoices or the entire provider account.

## Tests and evidence

```powershell
.venv/Scripts/python -m unittest discover -q
.venv/Scripts/python demo_evidence.py
```

Four synthetic references cover two exact EAD paths and two expected input rejections. Tests cover restart in a separate process, bounded tool recovery, expiry/scope isolation, uncertain-call stopping, usage accounting through mocked responses, governance blocking and aggregate LGD comparison contracts. Generated evidence remains local under ignored paths.

## Next steps

Verify the paired LGD evaluation sample and data timing, then demonstrate a capped live model-driven workflow. Improve economic outcome definitions only when supporting recovery/cost data exist. Keep observed evidence separate from proposed capabilities.
