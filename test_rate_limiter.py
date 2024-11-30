import asyncio
import time
import httpx


async def test_rate_limiter():
    print("Starting rate limit test...")
    async with httpx.AsyncClient() as client:
        responses = []
        for i in range(10):  
            try:
                response = await client.get('http://localhost:8000/test/rate-limit')
                status = response.status_code
                responses.append(status)
                print(f"Request {i+1}: Status {status}")
                if status == 429:
                    print(f"Rate limit hit: {response.json()['detail']}")
            except Exception as e:
                print(f"Request {i+1} failed: {e}")
            await asyncio.sleep(0.1)

        try:
            status = await client.get('http://localhost:8000/test/rate-limit-status')
            print("\nRate Limiter Status:")
            print(status.json())
        except Exception as e:
            print(f"Failed to get rate limiter status: {e}")

        success_count = responses.count(200)
        limited_count = responses.count(429)
        print("\nTest Summary:")
        print(f"Successful requests: {success_count}")
        print(f"Rate limited requests: {limited_count}")

if __name__ == "__main__":
    print("Ensuring FastAPI server is running...")
    print("Starting test in 3 seconds...")
    time.sleep(3)
    asyncio.run(test_rate_limiter())