from services import OpenAiService

tables = {
    "users": "Table containing user information and credentials",
    "datacenters": "Table containing datacenter locations and specifications",
    "connections": "Table tracking connections between users and datacenters"
}

async def main():
    print("Hello from s3e3!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
