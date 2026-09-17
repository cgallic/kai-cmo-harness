"""Located, source-backed data pulls for auditing a third-party local business.

Used by the ``/kai-local-audit`` skill. Every pull writes a raw artifact and
registers its sources and metrics in the same ``audit-data.json`` dataset that
``scripts.audit.collect`` produces, so the provenance lint covers it.

Entry points::

    python -m scripts.local_audit.pulls <command> --config <cfg.json> --out <audit-dir>
    python -m scripts.local_audit.checks <command> --config <cfg.json> --out <audit-dir>

Config shape: ``examples/local-audit-config.example.json``.
Playbook: ``harness/references/local-audit-playbook.md``.
"""
