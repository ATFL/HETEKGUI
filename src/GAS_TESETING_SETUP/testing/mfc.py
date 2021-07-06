import asyncio
from mfc import FlowController


class MFC:
    def __init__(self, IP):
        self.IP = IP
        self.mfc = FlowController(self.IP)

    async def get(self):
        async with self.MFC:
            print(await self.mfc.get())


# await fc.set(10)
# await fc.open()   # set to max flow
# await fc.close()  # set to zero flow
#
# await fc.set_gas('N2')
#
# await fc.set_display('flow')

def main():
    MFC1 = MFC('192.168.1.255')
    asyncio.run(MFC1.get())


if __name__ == "__main__":
    main()
