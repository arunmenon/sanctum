"""Local protocol fixture. No model calls, benchmark answers or gold access."""
import argparse
import asyncio
import json
import sys

from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client


def emit(event):
    print(json.dumps(event),flush=True)


async def run(config_path):
    prompt=sys.stdin.read()
    config=json.load(open(config_path))['mcpServers']['evidence']
    async with stdio_client(StdioServerParameters(command=config['command'],args=config['args'])) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            tools=(await session.list_tools()).tools
            emit(dict(type='system',subtype='init',tools=['mcp__evidence__'+t.name for t in tools]))
            task=prompt.partition('\n\nTask:\n')[2].partition('\nCaller requirements:\n')[0]
            tool=next(t for t in tools if 'query' in t.inputSchema.get('properties',{}))
            async def call(tool,args,number):
                emit(dict(type='assistant',message=dict(id=f'fixture-message-{number}',content=[dict(
                    type='tool_use',id=f'fixture-call-{number}',name=tool.name,input=args)])))
                result=await session.call_tool(tool.name,args)
                return result.structuredContent or json.loads(next(c.text for c in result.content if c.type=='text'))
            result=await call(tool,{'query':(task or prompt)[:500]},1)
            if tool.name!='sanctum_retrieve':
                # Discover the versioned file through public search results; no
                # corpus files, fixed repository names or private gold are read.
                unit=next((u for u in result.get('evidence',[]) if u.get('metadata',{}).get('path')),None)
                fetch=next((t for t in tools if t.name.startswith(tool.name.partition('__')[0]+'__')
                    and 'path' in t.inputSchema.get('required',[])),None)
                if unit and fetch:
                    args={'path':unit['metadata']['path']}
                    if 'ref' in fetch.inputSchema.get('properties',{}):args['ref']=unit['version']
                    await call(fetch,args,2)
            # Do not invent substantive task success. This only proves a runnable
            # transport and saved evidence flow across configurable corpora.
            answer=dict(schema_version=1,answer='Protocol fixture retrieved evidence; substantive investigation was not performed.',
                claims=[],uncertainties=['No model inference in this fixture.'],unmet_requirements=['Substantive task work.'])
            emit(dict(type='assistant',message=dict(id='fixture-final',content=[dict(type='text',text=json.dumps(answer))])))
            emit(dict(type='result',subtype='success',result=json.dumps(answer),usage={},total_cost_usd=0))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--mcp-config',required=True)
    asyncio.run(run(parser.parse_args().mcp_config))
