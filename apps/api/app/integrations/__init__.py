"""External integrations (Receita, SMS, SES, geocoding) behind adapters.

Each integration is a `Protocol` (base.py) with an httpx implementation and a
configurable Stub. `factory.py` returns the Stub for environment in {dev, test}
so the suite NEVER touches the network (Pitfall 1 / Gate 5).
"""
