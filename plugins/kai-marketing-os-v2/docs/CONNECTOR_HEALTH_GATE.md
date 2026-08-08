# Connector Health Gate (OSS MVP)

The connector health gate runs before live action execution and decides whether the action should:

- continue (`healthy`)
- continue with warning for low-risk actions (`unverified`, `stale`, `degraded`)
- block (`missing`, `error`, or medium/high risk with degraded health)

States:

- `missing`
- `unverified`
- `healthy`
- `degraded`
- `stale`
- `error`

## Python usage

```python
from kai.runtime.connector_health import evaluate_connector_health_gate
from kai.runtime.integrations import IntegrationRegistry

registry = IntegrationRegistry()
integrations = registry.list_for_brand("brand_demo", channel="website")

decision = evaluate_connector_health_gate(
    integrations,
    required_scopes=["write"],
    risk_tier="medium",
)
print(decision)
```

## CLI-style one-liner

```powershell
python -c "from kai.runtime.integrations import IntegrationRegistry; from kai.runtime.connector_health import evaluate_connector_health_gate; r=IntegrationRegistry(); i=r.list_for_brand('brand_demo', channel='website'); print(evaluate_connector_health_gate(i, required_scopes=['write'], risk_tier='medium'))"
```
