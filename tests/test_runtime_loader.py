"""Tests for the Kai runtime workspace and gateway integration."""

import asyncio
import contextlib
import types
import os
import sys
import tempfile
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import scripts.harness_config as harness_config
from kai.runtime import RuntimeStore
from kai.runtime.loader import load_workspace_profile
from gateway.models import JobStatus


def _with_config(yaml_content: str):
    """Context manager that points the runtime at a temp config.yaml."""
    import contextlib

    @contextlib.contextmanager
    def ctx():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as handle:
            handle.write(textwrap.dedent(yaml_content))
            handle.flush()
            previous = os.environ.get("CMO_CONFIG_PATH")
            os.environ["CMO_CONFIG_PATH"] = handle.name
            harness_config._config = None
            load_workspace_profile.cache_clear()
            try:
                yield Path(handle.name)
            finally:
                if previous is None:
                    os.environ.pop("CMO_CONFIG_PATH", None)
                else:
                    os.environ["CMO_CONFIG_PATH"] = previous
                harness_config._config = None
                load_workspace_profile.cache_clear()
                try:
                    os.unlink(handle.name)
                except OSError:
                    pass

    return ctx()


@contextlib.contextmanager
def _with_runtime_store(tmpdir: str):
    """Point the process-wide runtime store at a temp directory."""
    import kai.runtime.store as runtime_store_module

    previous = runtime_store_module._DEFAULT_RUNTIME_STORE
    runtime_store = RuntimeStore(base_dir=Path(tmpdir) / "runtime")
    runtime_store_module._DEFAULT_RUNTIME_STORE = runtime_store
    try:
        yield runtime_store
    finally:
        runtime_store_module._DEFAULT_RUNTIME_STORE = previous


@contextlib.contextmanager
def _with_fastapi_stub():
    """Provide the minimum FastAPI symbols needed to import router modules."""
    previous = sys.modules.get("fastapi")

    class _HTTPException(Exception):
        def __init__(self, status_code=None, detail=None):
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail

    class _APIRouter:
        def get(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator

        def post(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator

        def delete(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator

    fastapi_stub = types.ModuleType("fastapi")
    fastapi_stub.APIRouter = _APIRouter
    fastapi_stub.HTTPException = _HTTPException
    sys.modules["fastapi"] = fastapi_stub
    try:
        yield fastapi_stub
    finally:
        if previous is None:
            sys.modules.pop("fastapi", None)
        else:
            sys.modules["fastapi"] = previous


@contextlib.contextmanager
def _with_job_queue(tmpdir: str):
    """Swap the gateway job queue for an isolated temp-backed queue."""
    import gateway.jobs as gateway_jobs
    from gateway.jobs import JobQueue

    previous_queue = gateway_jobs.job_queue
    queue = JobQueue(db_path=Path(tmpdir) / "jobs.db", max_workers=1)
    gateway_jobs.job_queue = queue
    try:
        with _with_fastapi_stub():
            import gateway.routers.jobs as jobs_router

            jobs_router.job_queue = queue
            try:
                yield queue
            finally:
                jobs_router.job_queue = previous_queue
    finally:
        queue.shutdown()
        gateway_jobs.job_queue = previous_queue


def test_workspace_profile_builds_runtime_brands():
    """Runtime workspace should infer archetypes and module overlays from products."""
    yaml_content = """
    workspace:
      id: "kai-test"
      name: "Kai Test Runtime"
      primary_user: "operator_saas"
      product_mode: "clone"
      surfaces: ["local", "remote"]

    sites:
      gsc_urls:
        truenorth: "sc-domain:truenorthhvac.com"
      ga4_properties:
        truenorth: "123456"

    site_persona_defaults:
      truenorth:
        primary: "Competent Cog"
        secondary: "System Manager"

    products:
      - id: truenorth
        name: "TrueNorth HVAC"
        url: "https://truenorthhvac.com"
        description: "Residential HVAC installation and repair with same-day emergency service across multiple offices in North Texas."
        proof_points: |
          - Same-day emergency service
          - Offices in Dallas and Plano
    """
    with _with_config(yaml_content):
        workspace = load_workspace_profile()
        brand = workspace.get_brand("truenorth")

        assert workspace.workspace_id == "kai-test"
        assert brand is not None
        assert brand.primary_archetype == "local-service"
        assert "multi-location" in brand.module_ids
        assert brand.gsc_site == "sc-domain:truenorthhvac.com"
        assert brand.ga_property == "123456"


def test_gateway_config_reads_runtime_brands():
    """Gateway config should expose runtime brands even without clients_config.json."""
    yaml_content = """
    workspace:
      id: "kai-test"
      name: "Kai Test Runtime"

    products:
      - id: glowcraft
        name: "GlowCraft"
        description: "DTC skincare ecommerce brand with Shopify storefront and retention email flows."
        proof_points: |
          - 4.8 star average
          - Hero product is Vitamin C Serum
    """
    with _with_config(yaml_content):
        import gateway.config as gateway_config

        gateway_config.config._workspace_profile = None
        gateway_config.config._clients_config = None

        brand = gateway_config.config.get_client("glowcraft")
        clients = gateway_config.config.get_all_clients()

        assert brand is not None
        assert brand["category"] == "brand"
        assert brand["primary_archetype"] == "ecommerce"
        assert brand["module_ids"] == ["ecommerce"]
        assert any(client["id"] == "glowcraft" for client in clients)


def test_runtime_store_persists_runs_artifacts_and_state():
    """Runtime store should persist run state, artifacts, and lineage on disk."""
    yaml_content = """
    workspace:
      id: "kai-test"
      name: "Kai Test Runtime"

    products:
      - id: glowcraft
        name: "GlowCraft"
        description: "DTC skincare ecommerce brand with Shopify storefront and retention email flows."
        proof_points: |
          - 4.8 star average
          - Hero product is Vitamin C Serum
    """
    with _with_config(yaml_content):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = RuntimeStore(base_dir=Path(tmpdir) / "runtime")

            root_run = store.start_run(
                {
                    "intent": "Launch a paid social campaign",
                    "workflow": "kai-ad-campaign",
                    "brand_id": "glowcraft",
                    "surface": "remote",
                    "inputs": {"keyword": "vitamin c serum"},
                    "metadata": {"source": "test"},
                }
            )
            child_run = store.start_run(
                {
                    "intent": "Revise the campaign brief",
                    "workflow": "kai-ad-campaign",
                    "brand_id": "glowcraft",
                    "surface": "remote",
                    "inputs": {"revision": 1},
                },
                parent_run_id=root_run["run_id"],
            )

            artifact = store.record_artifact(
                {
                    "artifact_type": "brief",
                    "brand_id": "glowcraft",
                    "workflow": "kai-ad-campaign",
                    "data": {"headline": "Vitamin C that actually converts"},
                },
                run_id=root_run["run_id"],
            )
            store.complete_run(
                root_run["run_id"],
                outputs={"artifact_id": artifact["artifact_id"]},
                metadata={"approval_state": "held"},
            )

            state = store.snapshot_state()
            reload_store = RuntimeStore(base_dir=Path(tmpdir) / "runtime")

            assert reload_store.get_run(root_run["run_id"])["status"] == "completed"
            assert child_run["ancestor_run_ids"] == [root_run["run_id"]]
            assert artifact["source_run"] == root_run["run_id"]
            assert artifact["lineage_run_ids"] == [root_run["run_id"]]
            assert reload_store.get_run(root_run["run_id"]) is not None
            assert reload_store.get_artifact(artifact["artifact_id"]) is not None
            assert reload_store.get_run_lineage(child_run["run_id"]) == [
                root_run["run_id"],
                child_run["run_id"],
            ]
            assert state["latest_run_ids_by_brand"]["glowcraft"] == root_run["run_id"]
            assert state["latest_run_ids_by_brand_workflow"]["glowcraft:kai-ad-campaign"] == root_run["run_id"]
            assert child_run["run_id"] in state["active_run_ids"]
            assert state["latest_artifact_ids_by_brand"]["glowcraft"] == artifact["artifact_id"]
            assert state["latest_artifact_ids_by_brand_workflow"]["glowcraft:kai-ad-campaign"] == artifact["artifact_id"]


def test_gateway_job_layer_uses_runtime_store_artifacts_and_canonical_run():
    """Gateway jobs should expose canonical run fields and prefer runtime artifacts."""
    yaml_content = """
    workspace:
      id: "kai-test"
      name: "Kai Test Runtime"

    products:
      - id: glowcraft
        name: "GlowCraft"
        description: "DTC skincare ecommerce brand with Shopify storefront and retention email flows."
        proof_points: |
          - 4.8 star average
          - Hero product is Vitamin C Serum
    """
    with _with_config(yaml_content):
        with tempfile.TemporaryDirectory() as tmpdir:
            with _with_runtime_store(tmpdir) as runtime_store:
                with _with_job_queue(tmpdir) as job_queue:
                    import gateway.config as gateway_config
                    import gateway.routers.jobs as jobs_router

                    gateway_config.config._workspace_profile = None
                    gateway_config.config._clients_config = None

                    job_id = job_queue.create_job(
                        command="generate",
                        client="glowcraft",
                        options={
                            "format": "blog",
                            "site": "glowcraft",
                            "keyword": "vitamin c serum",
                            "brand_id": "glowcraft",
                            "workflow": "kai-campaign",
                        },
                        run_request={
                            "intent": "Generate blog for glowcraft: vitamin c serum",
                            "workflow": "kai-campaign",
                            "brand_id": "glowcraft",
                            "surface": "remote",
                            "module_set": ["ecommerce"],
                            "inputs": {
                                "format": "blog",
                                "site": "glowcraft",
                                "keyword": "vitamin c serum",
                            },
                            "metadata": {"source": "test"},
                        },
                    )
                    runtime_store.start_run(
                        {
                            "intent": "Generate blog for glowcraft: vitamin c serum",
                            "workflow": "kai-campaign",
                            "brand_id": "glowcraft",
                            "surface": "remote",
                            "module_set": ["ecommerce"],
                            "inputs": {"keyword": "vitamin c serum"},
                            "metadata": {"source": "test"},
                        },
                        run_id=job_id,
                    )
                    brief = runtime_store.record_artifact(
                        {
                            "artifact_type": "brief",
                            "brand_id": "glowcraft",
                            "workflow": "kai-campaign",
                            "module_set": ["ecommerce"],
                            "data": {"brief": {"angle": "Conversion-first"}},
                        },
                        run_id=job_id,
                    )
                    draft = runtime_store.record_artifact(
                        {
                            "artifact_type": "draft",
                            "brand_id": "glowcraft",
                            "workflow": "kai-campaign",
                            "module_set": ["ecommerce"],
                            "parent_artifact_id": brief["artifact_id"],
                            "data": {"content": "Draft body for the campaign."},
                        },
                        run_id=job_id,
                        parent_artifact_id=brief["artifact_id"],
                    )
                    runtime_store.complete_run(
                        job_id,
                        status="approved",
                        outputs={"artifact_refs": {"brief": brief["artifact_id"], "draft": draft["artifact_id"]}},
                        metadata={"approval_policy": "default"},
                    )
                    job_queue.record_artifact(
                        run_id=job_id,
                        artifact_type="brief",
                        brand_id="glowcraft",
                        workflow="kai-campaign",
                        payload={"brief": {"angle": "Conversion-first"}},
                        job_id=job_id,
                        module_set=["ecommerce"],
                    )
                    job_queue.record_artifact(
                        run_id=job_id,
                        artifact_type="draft",
                        brand_id="glowcraft",
                        workflow="kai-campaign",
                        payload={"content": "Draft body for the campaign."},
                        job_id=job_id,
                        module_set=["ecommerce"],
                    )
                    job_queue.update_job(
                        job_id,
                        status=JobStatus.COMPLETED,
                        completed_at=job_queue.get_job(job_id).created_at,
                        result={
                            "run_id": job_id,
                            "artifact_refs": {"brief": brief["artifact_id"], "draft": draft["artifact_id"]},
                        },
                    )

                    job = job_queue.get_job(job_id)
                    assert job.status.value == "completed"
                    assert job.run_id == job_id
                    assert job.workflow == "kai-campaign"
                    assert job.brand_id == "glowcraft"
                    assert job.surface.value == "remote"
                    assert job.module_set == ["ecommerce"]
                    assert len(job.artifact_ids) == 2

                    runtime_job = runtime_store.get_run(job_id)
                    assert runtime_job is not None
                    assert runtime_job["status"] == "approved"
                    assert runtime_store.list_artifacts(run_id=job_id)

                    original_list_artifacts = jobs_router.job_queue.list_artifacts

                    def _fail_if_called(*args, **kwargs):
                        raise AssertionError("gateway fallback should not be needed when runtime artifacts exist")

                    jobs_router.job_queue.list_artifacts = _fail_if_called
                    try:
                        artifacts_response = asyncio.run(jobs_router.list_job_artifacts(job_id))
                    finally:
                        jobs_router.job_queue.list_artifacts = original_list_artifacts

                    artifacts = artifacts_response.data["artifacts"]
                    assert len(artifacts) == 2
                    assert {artifact["artifact_type"] for artifact in artifacts} == {"brief", "draft"}
                    assert artifacts[0]["source_run"] == job_id


def test_runtime_router_exposes_canonical_state_and_lineage():
    """Runtime router should return the canonical state snapshot from the runtime store."""
    yaml_content = """
    workspace:
      id: "kai-test"
      name: "Kai Test Runtime"

    products:
      - id: truenorth
        name: "TrueNorth HVAC"
        description: "Residential HVAC installation and repair with same-day emergency service."
        proof_points: |
          - Same-day emergency service
          - Offices in Dallas and Plano
    """
    with _with_config(yaml_content):
        with tempfile.TemporaryDirectory() as tmpdir:
            with _with_runtime_store(tmpdir) as runtime_store:
                with _with_fastapi_stub():
                    import gateway.routers.runtime as runtime_router

                    previous_getter = runtime_router.get_default_runtime_store
                    runtime_router.get_default_runtime_store = lambda: runtime_store
                    try:
                        root_run = runtime_store.start_run(
                            {
                                "intent": "Launch a local SEO audit",
                                "workflow": "kai-seo-audit",
                                "brand_id": "truenorth",
                                "surface": "local",
                                "inputs": {"keyword": "hvac repair"},
                                "metadata": {"source": "test"},
                            }
                        )
                        artifact = runtime_store.record_artifact(
                            {
                                "artifact_type": "audit_findings",
                                "brand_id": "truenorth",
                                "workflow": "kai-seo-audit",
                                "data": {"issues": ["missing service-area coverage"]},
                            },
                            run_id=root_run["run_id"],
                        )
                        runtime_store.complete_run(root_run["run_id"], outputs={"artifact_id": artifact["artifact_id"]})
                        state = runtime_store.snapshot_state()

                        workspace = asyncio.run(runtime_router.get_workspace())
                        brands = asyncio.run(runtime_router.list_brands())
                        modules = asyncio.run(runtime_router.list_modules())
                        runtime_state = asyncio.run(runtime_router.get_runtime_state())
                        runs = asyncio.run(runtime_router.list_runs(brand_id="truenorth"))
                        artifacts = asyncio.run(runtime_router.list_artifacts(run_id=root_run["run_id"]))
                        fetched_run = asyncio.run(runtime_router.get_run(root_run["run_id"]))
                        fetched_artifact = asyncio.run(runtime_router.get_artifact(artifact["artifact_id"]))

                        assert workspace["workspace_id"] == "kai-test"
                        assert brands["count"] == 1
                        assert any(brand["id"] == "truenorth" for brand in brands["brands"])
                        assert modules["count"] >= 1
                        assert runtime_state["workspace_id"] == "kai-test"
                        assert runtime_state["latest_run_ids_by_brand"]["truenorth"] == root_run["run_id"]
                        assert state["latest_artifact_ids_by_brand"]["truenorth"] == artifact["artifact_id"]
                        assert runs["count"] == 1
                        assert runs["runs"][0]["run_id"] == root_run["run_id"]
                        assert artifacts["count"] == 1
                        assert artifacts["artifacts"][0]["artifact_id"] == artifact["artifact_id"]
                        assert fetched_run["run_id"] == root_run["run_id"]
                        assert fetched_artifact["artifact_id"] == artifact["artifact_id"]
                    finally:
                        runtime_router.get_default_runtime_store = previous_getter


def test_approval_lifecycle_transitions():
    """Approval mutations should transition run status and record history."""
    yaml_content = """
    workspace:
      id: "kai-test"
      name: "Kai Test Runtime"

    products:
      - id: glowcraft
        name: "GlowCraft"
        description: "DTC skincare ecommerce brand."
        proof_points: |
          - 4.8 star average
    """
    with _with_config(yaml_content):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = RuntimeStore(base_dir=Path(tmpdir) / "runtime")

            run = store.start_run({
                "intent": "Test approval lifecycle",
                "workflow": "content-generate",
                "brand_id": "glowcraft",
                "surface": "local",
                "inputs": {"keyword": "serum"},
            })
            run_id = run["run_id"]

            # Complete run in draft state
            store.complete_run(run_id, status="draft", outputs={"content": "Draft body"})

            # Hold the run
            held = store.hold_run(run_id, note="Needs legal review")
            assert held["status"] == "held"
            history = held["metadata"]["approval_history"]
            assert len(history) == 1
            assert history[0]["action"] == "held"
            assert history[0]["note"] == "Needs legal review"

            # Request revision — moves back to draft
            revised = store.request_revision(run_id, note="Fix the intro paragraph")
            assert revised["status"] == "draft"
            assert revised["completed_at"] is None
            assert len(revised["metadata"]["approval_history"]) == 2
            assert revised["metadata"]["approval_history"][1]["action"] == "revision_requested"

            # Approve
            approved = store.approve_run(run_id, note="LGTM")
            assert approved["status"] == "approved"
            assert len(approved["metadata"]["approval_history"]) == 3
            assert approved["metadata"]["approval_history"][2]["action"] == "approved"

            # Verify bundle has approval context
            bundle = store.get_run_bundle(run_id)
            assert bundle is not None
            assert bundle["approval"]["status"] == "approved"
            assert "memory_updates" in bundle

            # Cannot approve a failed run
            run2 = store.start_run({
                "intent": "Test reject",
                "workflow": "content-generate",
                "brand_id": "glowcraft",
                "surface": "local",
            })
            store.complete_run(run2["run_id"], status="draft")
            rejected = store.reject_run(run2["run_id"], note="Off-brand")
            assert rejected["status"] == "failed"
            assert rejected["outputs"]["rejection_note"] == "Off-brand"

            # Rejected run cannot be approved (status=failed, not in actionable set)
            try:
                store.approve_run(run2["run_id"])
                assert False, "Should have raised ValueError"
            except ValueError:
                pass


def test_resume_run_creates_child_with_lineage():
    """resume_run should create a linked child run with merged inputs."""
    yaml_content = """
    workspace:
      id: "kai-test"
      name: "Kai Test Runtime"

    products:
      - id: glowcraft
        name: "GlowCraft"
        description: "DTC skincare ecommerce brand."
    """
    with _with_config(yaml_content):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = RuntimeStore(base_dir=Path(tmpdir) / "runtime")

            parent = store.start_run({
                "intent": "Original run",
                "workflow": "content-generate",
                "brand_id": "glowcraft",
                "surface": "remote",
                "inputs": {"keyword": "serum", "format": "blog"},
            })
            store.complete_run(parent["run_id"], status="held")

            child = store.resume_run(
                parent["run_id"],
                inputs_override={"keyword": "updated serum guide"},
            )
            assert child["status"] == "running"
            assert child["parent_run_id"] == parent["run_id"]
            assert parent["run_id"] in child["ancestor_run_ids"]
            assert child["inputs"]["keyword"] == "updated serum guide"
            assert child["inputs"]["format"] == "blog"
            assert child["metadata"]["resumed_from"] == parent["run_id"]

            lineage = store.get_run_lineage(child["run_id"])
            assert lineage == [parent["run_id"], child["run_id"]]


def test_memory_writeback_on_approval():
    """Approved runs with learned patterns should write memory entries to disk."""
    yaml_content = """
    workspace:
      id: "kai-test"
      name: "Kai Test Runtime"

    products:
      - id: glowcraft
        name: "GlowCraft"
        description: "DTC skincare ecommerce brand."
    """
    with _with_config(yaml_content):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = RuntimeStore(base_dir=Path(tmpdir) / "runtime")

            run = store.start_run({
                "intent": "Content gen with learnings",
                "workflow": "content-generate",
                "brand_id": "glowcraft",
                "surface": "local",
                "inputs": {"keyword": "serum"},
            })
            run_id = run["run_id"]

            store.record_artifact(
                {
                    "artifact_type": "learned_pattern",
                    "brand_id": "glowcraft",
                    "workflow": "content-generate",
                    "data": {"pattern": "Short intros convert better", "confidence": 0.85},
                },
                run_id=run_id,
            )
            store.complete_run(
                run_id,
                status="draft",
                outputs={
                    "content": "Final body",
                    "gate_report": {"score": 14, "grade": "A", "strengths": ["unique angle"]},
                    "memory_updates": [
                        {"category": "voice_constraint", "data": {"rule": "Never open with a question"}},
                    ],
                },
            )

            # Approve — triggers writeback
            store.approve_run(run_id)

            memory_dir = Path(tmpdir) / "runtime" / "memory"
            assert memory_dir.exists()
            memory_files = list(memory_dir.glob("*.json"))
            assert len(memory_files) >= 1

            # Bundle should also reflect memory updates
            bundle = store.get_run_bundle(run_id)
            assert len(bundle["memory_updates"]) >= 2  # learned_pattern + voice_constraint


def test_canonical_bundle_shape():
    """Bundle must contain all six canonical fields."""
    yaml_content = """
    workspace:
      id: "kai-test"
      name: "Kai Test Runtime"

    products:
      - id: glowcraft
        name: "GlowCraft"
        description: "DTC skincare ecommerce brand."
    """
    with _with_config(yaml_content):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = RuntimeStore(base_dir=Path(tmpdir) / "runtime")

            run = store.start_run({
                "intent": "Test bundle shape",
                "workflow": "content-generate",
                "brand_id": "glowcraft",
                "surface": "local",
            })
            store.complete_run(run["run_id"], status="approved")

            bundle = store.get_run_bundle(run["run_id"])
            assert bundle is not None
            required_keys = {"run", "lineage", "artifacts", "approval", "observability", "memory_updates"}
            assert required_keys == set(bundle.keys())
            assert bundle["approval"]["status"] == "approved"
            assert isinstance(bundle["memory_updates"], list)


def test_approval_endpoints_via_runtime_router():
    """Runtime router approval endpoints should transition run state correctly."""
    yaml_content = """
    workspace:
      id: "kai-test"
      name: "Kai Test Runtime"

    products:
      - id: truenorth
        name: "TrueNorth HVAC"
        description: "Residential HVAC installation and repair."
    """
    with _with_config(yaml_content):
        with tempfile.TemporaryDirectory() as tmpdir:
            with _with_runtime_store(tmpdir) as runtime_store:
                with _with_fastapi_stub():
                    import gateway.routers.runtime as runtime_router

                    previous_getter = runtime_router.get_default_runtime_store
                    runtime_router.get_default_runtime_store = lambda: runtime_store
                    try:
                        run = runtime_store.start_run({
                            "intent": "Router approval test",
                            "workflow": "kai-audit",
                            "brand_id": "truenorth",
                            "surface": "remote",
                        })
                        run_id = run["run_id"]
                        runtime_store.complete_run(run_id, status="draft")

                        # Hold via endpoint
                        hold_resp = asyncio.run(runtime_router.hold_run(run_id, note="Review needed"))
                        assert hold_resp["status"] == "held"

                        # Revise via endpoint
                        revise_resp = asyncio.run(runtime_router.request_revision(run_id, note="Fix findings"))
                        assert revise_resp["status"] == "draft"

                        # Approve via endpoint
                        approve_resp = asyncio.run(runtime_router.approve_run(run_id))
                        assert approve_resp["status"] == "approved"
                        assert "memory_updates" in approve_resp

                        # Verify bundle endpoint
                        bundle = asyncio.run(runtime_router.get_run_bundle(run_id))
                        assert bundle["approval"]["status"] == "approved"
                        assert "memory_updates" in bundle

                        # Resume via endpoint
                        run2 = runtime_store.start_run({
                            "intent": "Resumable run",
                            "workflow": "kai-audit",
                            "brand_id": "truenorth",
                            "surface": "remote",
                        })
                        runtime_store.complete_run(run2["run_id"], status="held")
                        resume_resp = asyncio.run(
                            runtime_router.resume_run(run2["run_id"], inputs_override={"keyword": "hvac repair"})
                        )
                        assert resume_resp["parent_run_id"] == run2["run_id"]
                        assert resume_resp["status"] == "running"

                        # Reject via endpoint
                        run3 = runtime_store.start_run({
                            "intent": "Rejectable run",
                            "workflow": "kai-audit",
                            "brand_id": "truenorth",
                            "surface": "remote",
                        })
                        runtime_store.complete_run(run3["run_id"], status="draft")
                        reject_resp = asyncio.run(runtime_router.reject_run(run3["run_id"], note="Off brand"))
                        assert reject_resp["status"] == "failed"

                    finally:
                        runtime_router.get_default_runtime_store = previous_getter


if __name__ == "__main__":
    test_workspace_profile_builds_runtime_brands()
    test_gateway_config_reads_runtime_brands()
    test_runtime_store_persists_runs_artifacts_and_state()
    test_gateway_job_layer_uses_runtime_store_artifacts_and_canonical_run()
    test_runtime_router_exposes_canonical_state_and_lineage()
    test_approval_lifecycle_transitions()
    test_resume_run_creates_child_with_lineage()
    test_memory_writeback_on_approval()
    test_canonical_bundle_shape()
    test_approval_endpoints_via_runtime_router()
    print("All runtime tests passed!")
