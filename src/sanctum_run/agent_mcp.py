"""Session-bound agent-facing MCP surface over the existing gateway.

The controller owns identity and request IDs. Agents receive neither caller
tokens nor broker tools, and may call Sanctum repeatedly within the same limits.
"""
from __future__ import annotations

import time
import uuid
from typing import Any

import anyio
from mcp import types
from mcp.server.lowlevel import Server

from sanctum_contracts import RetrieveRequest
from sanctum_run.delivery import DeliveryBudget, EvidenceNormalizer
from sanctum_run.gateway import HubGateway
from sanctum_run.sut import SUTContext, SystemUnderTest


class AgentMCP:
    def __init__(self, gateway: HubGateway, caller_token: str, arm: str,
                 normalizer: EvidenceNormalizer, budget: DeliveryBudget,
                 *, sut: SystemUnderTest | None = None, deadline_seconds: float = 120,
                 max_calls: int = 32):
        if arm not in ('direct','sanctum') or (arm == 'sanctum' and sut is None):
            raise ValueError('invalid arm or missing Sanctum runtime')
        if max_calls <= 0 or deadline_seconds <= 0:
            raise ValueError('invalid session bounds')
        self.gateway,self._caller,self.arm = gateway,caller_token,arm
        self.normalizer,self.budget,self.sut = normalizer,budget,sut
        self.deadline=time.monotonic()+deadline_seconds
        self.max_calls=max_calls
        self.calls: list[dict] = []
        self._targets: dict[str,tuple[str,str]] = {}
        self._tools: list[types.Tool] = []
        self._scopes: set[anyio.CancelScope] = set()
        self.closed=False
        self.server: Server = Server('sanctum-agent-evidence')

    async def initialize(self):
        if self.arm == 'direct':
            for hub in self.gateway.hub_ids:
                for tool in await self.gateway.list_hub_tools(hub):
                    name=f'{hub}__{tool.name}'
                    if name in self._targets:
                        raise ValueError('ambiguous public tool name')
                    self._targets[name]=(hub,tool.name)
                    self._tools.append(types.Tool(name=name,description=tool.description,inputSchema=tool.inputSchema))
        else:
            self._tools=[types.Tool(name='sanctum_retrieve',description='Retrieve authorized evidence across knowledge sources.',
                inputSchema=dict(type='object',additionalProperties=False,required=['query'],properties=dict(
                    query=dict(type='string'),mode=dict(enum=['scoped','explore','verify'],default='explore'),
                    scope=dict(type='string'),as_of=dict(type='string'),environment=dict(type='string'))))]

        @self.server.list_tools()
        async def list_tools():
            return list(self._tools)

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str,Any]):
            return await self.dispatch(name,arguments)
        return self

    @property
    def inventory(self):
        return [t.name for t in self._tools]

    async def dispatch(self, name: str, arguments: dict[str,Any]):
        sequence=await self.budget.issue()
        request_id='agent-'+uuid.uuid4().hex
        trace=dict(sequence=sequence,tool=name,request_id=request_id,
                   public_arguments={k:v for k,v in arguments.items() if k not in ('caller_token','token','api_key','credential','secret','password')})
        handle=None
        try:
            if self.closed:
                return await self.budget.deliver(sequence,[],error='session_closed')
            if sequence >= self.max_calls:
                return await self.budget.deliver(sequence,[],error='call_budget_exhausted')
            if self.budget.remaining <= 0:
                return await self.budget.deliver(sequence,[],error='evidence_budget_exhausted')
            if name not in self.inventory:
                return await self.budget.deliver(sequence,[],error='tool_not_allowed')
            remaining=self.deadline-time.monotonic()
            if remaining <= 0:
                return await self.budget.deliver(sequence,[],error='deadline_exceeded')
            handle=self.gateway.handle(request_id,self._caller)
            with anyio.fail_after(remaining) as cancel_scope:
                self._scopes.add(cancel_scope)
                try:
                    if self.arm == 'direct':
                        hub,tool=self._targets[name]
                        payload=await handle.call(hub,tool,arguments)
                        units=self.normalizer.normalize(hub,payload)
                    else:
                        if set(arguments)-{'query','mode','scope','as_of','environment'}:
                            return await self.budget.deliver(sequence,[],error='invalid_argument')
                        request=RetrieveRequest(request_id=request_id,query=arguments['query'],
                            mode=arguments.get('mode','explore'),scope=arguments.get('scope'),
                            as_of=arguments.get('as_of'),environment=arguments.get('environment'),
                            budget_tokens=min(self.budget.remaining,self.budget.per_response),
                            deadline_ms=max(1,int(remaining*1000)))
                        response,receipt=await self.sut.retrieve(request,SUTContext(self._caller,handle))
                        trace['router_receipt']=receipt.model_dump(mode='json')
                        units=self.normalizer.normalize(None,response.model_dump(mode='json'))
                finally:
                    self._scopes.discard(cancel_scope)
            return await self.budget.deliver(sequence,units)
        except TimeoutError:
            return await self.budget.deliver(sequence,[],error='deadline_exceeded')
        except (ValueError,KeyError,TypeError):
            return await self.budget.deliver(sequence,[],error='invalid_argument')
        except Exception:
            # Provider/transport exception strings can contain credential material.
            return await self.budget.deliver(sequence,[],error='infrastructure_failure')
        finally:
            if handle is not None:
                self.gateway.release(handle)
            trace['backend_trace']=self.gateway.trace(request_id).model_dump(mode='json')
            self.calls.append(trace)

    async def close(self):
        self.closed=True
        for scope in tuple(self._scopes):
            scope.cancel()
        await self.budget.close()
