"""Credential-free stdio relay to the controller's private local MCP socket."""
import argparse
import asyncio
import sys


async def relay(path):
    reader, writer = await asyncio.open_unix_connection(path)
    async def inbound():
        while True:
            line = await asyncio.to_thread(sys.stdin.buffer.readline)
            if not line:
                break
            writer.write(line)
            await writer.drain()
        writer.close()

    async def outbound():
        while line := await reader.readline():
            sys.stdout.buffer.write(line)
            sys.stdout.buffer.flush()

    tasks=[asyncio.create_task(inbound()),asyncio.create_task(outbound())]
    try:
        await asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED)
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)
        writer.close()
        await writer.wait_closed()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--socket',required=True)
    asyncio.run(relay(parser.parse_args().socket))


if __name__=='__main__':
    main()
