"""Test-only `HubPort` for running `sanctum_ref` in process against a `HubGateway`.

Production runs use the out-of-process `ProcessSUT` and the gateway proxy; this port exists so
unit tests can drive the pipeline without spawning a process. It exposes the same three calls
the proxy serves (hub tools, caller access groups, capabilities) and nothing else."""
import json
from pathlib import Path

from sanctum_ref.config import load_arm
from sanctum_ref.pipeline import MemoryState, Retriever
from sanctum_ref.registry import RegistryUnavailable, load_registry

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "configs" / "matrix.yaml"
MANIFESTS = ROOT / "owners" / "manifests"
MEMORY_SEED = ROOT / "owners" / "memory_seed"


class GatewayPort:
    def __init__(self, gateway, request_id: str, handle, world_build_dir: Path):
        self._gateway = gateway
        self._request_id = request_id
        self._handle = handle
        self._world_build_dir = Path(world_build_dir)

    async def call(self, hub_id, tool, arguments):
        return await self._handle.call(hub_id, tool, arguments)

    async def caller_groups(self):
        self.reader = self._gateway.reader_ref(self._handle)
        return self._gateway.caller_groups(self._handle)

    async def change_events(self, after_seq):
        return self._gateway.change_events(self._handle, after_seq) or []

    async def capabilities(self):
        return {hub_id: json.loads((self._world_build_dir / "hubs" / hub_id / "capabilities.json").read_text())
                for hub_id in self._gateway.hub_ids}


class InProcessRef:
    """Runs `Retriever` under the runner's SUT protocol (tests only)."""

    def __init__(self, config_id: str, world_build_dir: Path, registry_dir: Path = MANIFESTS,
                 memory_seed: Path = MEMORY_SEED):
        self._arm = load_arm(MATRIX, config_id)
        self.memory = MemoryState(memory_seed)
        self._registry_dir = registry_dir
        self._world_build_dir = world_build_dir
        self.gateway = None

    def open(self, gateway, world_build_dir):
        self.gateway = gateway
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def _noop():
            yield self
        return _noop()

    async def retrieve(self, request, context):
        try:
            registry = load_registry(self._registry_dir)
        except RegistryUnavailable:
            registry = None
        port = GatewayPort(self.gateway, request.request_id, context.gateway, self._world_build_dir)
        return await Retriever(self._arm, registry, memory=self.memory).retrieve(request, port)
