#!/usr/bin/env python3
"""Test ChatGPT scraper to verify API fetches data correctly.

How to run manually:
    python tests/enes/chatgpt.py
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from brightdata import BrightDataClient


async def test_chatgpt_single_prompt():
    """Test ChatGPT single prompt."""

    print("=" * 60)
    print("CHATGPT SCRAPER TEST - Single Prompt")
    print("=" * 60)

    client = BrightDataClient()

    async with client.engine:
        scraper = client.scrape.chatgpt
        async with scraper.engine:
            print("\n🤖 Testing ChatGPT single prompt...")
            print("📋 Prompt: 'Explain async programming in Python in 2 sentences'")

            try:
                result = await scraper.prompt_async(
                    prompt="Explain async programming in Python in 2 sentences",
                    web_search=False,
                    poll_timeout=180
                )

                print(f"\n✅ API call succeeded")
                print(f"⏱️  Elapsed: {result.elapsed_ms():.2f}ms" if result.elapsed_ms() else "")

                print(f"\n📊 Result analysis:")
                print(f"   - result.success: {result.success}")
                print(f"   - result.data type: {type(result.data)}")

                if result.data:
                    print(f"\n✅ Got ChatGPT response:")
                    if isinstance(result.data, dict):
                        print(f"   - Response: {result.data.get('response', 'N/A')[:200]}...")
                        print(f"   - Prompt: {result.data.get('prompt', 'N/A')}")
                    elif isinstance(result.data, str):
                        print(f"   - Response: {result.data[:200]}...")
                    else:
                        print(f"   Data: {result.data}")
                else:
                    print(f"\n❌ No response data returned")

            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()


async def test_chatgpt_web_search():
    """Test ChatGPT prompt with web search enabled."""

    print("\n\n" + "=" * 60)
    print("CHATGPT SCRAPER TEST - Web Search")
    print("=" * 60)

    client = BrightDataClient()

    async with client.engine:
        scraper = client.scrape.chatgpt
        async with scraper.engine:
            print("\n🔍 Testing ChatGPT with web search...")
            print("📋 Prompt: 'What are the latest developments in AI in 2024?'")
            print("🌐 Web search: Enabled")

            try:
                result = await scraper.prompt_async(
                    prompt="What are the latest developments in AI in 2024?",
                    web_search=True,
                    poll_timeout=180
                )

                print(f"\n✅ API call succeeded")
                print(f"⏱️  Elapsed: {result.elapsed_ms():.2f}ms" if result.elapsed_ms() else "")

                print(f"\n📊 Result analysis:")
                print(f"   - result.success: {result.success}")
                print(f"   - result.data type: {type(result.data)}")

                if result.data:
                    print(f"\n✅ Got ChatGPT response with web search:")
                    if isinstance(result.data, dict):
                        print(f"   - Response: {result.data.get('response', 'N/A')[:200]}...")
                        print(f"   - Web search used: {result.data.get('web_search', False)}")
                    elif isinstance(result.data, str):
                        print(f"   - Response: {result.data[:200]}...")
                    else:
                        print(f"   Data: {result.data}")
                else:
                    print(f"\n❌ No response data returned")

            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()


async def test_chatgpt_multiple_prompts():
    """Test ChatGPT batch prompts."""

    print("\n\n" + "=" * 60)
    print("CHATGPT SCRAPER TEST - Multiple Prompts")
    print("=" * 60)

    client = BrightDataClient()

    async with client.engine:
        scraper = client.scrape.chatgpt
        async with scraper.engine:
            print("\n📝 Testing ChatGPT batch prompts...")
            print("📋 Prompts: ['What is Python?', 'What is JavaScript?']")

            try:
                result = await scraper.prompts_async(
                    prompts=[
                        "What is Python in one sentence?",
                        "What is JavaScript in one sentence?"
                    ],
                    web_searches=[False, False],
                    poll_timeout=180
                )

                print(f"\n✅ API call succeeded")
                print(f"⏱️  Elapsed: {result.elapsed_ms():.2f}ms" if result.elapsed_ms() else "")

                print(f"\n📊 Result analysis:")
                print(f"   - result.success: {result.success}")
                print(f"   - result.data type: {type(result.data)}")

                if result.data:
                    if isinstance(result.data, list):
                        print(f"\n✅ Got {len(result.data)} responses:")
                        for i, response in enumerate(result.data, 1):
                            print(f"\n   Response {i}:")
                            if isinstance(response, dict):
                                print(f"   - Prompt: {response.get('prompt', 'N/A')}")
                                print(f"   - Response: {response.get('response', 'N/A')[:100]}...")
                            else:
                                print(f"   - Response: {str(response)[:100]}...")
                    else:
                        print(f"   Data: {result.data}")
                else:
                    print(f"\n❌ No responses returned")

            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    print("\n🚀 Starting ChatGPT Scraper Tests\n")
    asyncio.run(test_chatgpt_single_prompt())
    asyncio.run(test_chatgpt_web_search())
    asyncio.run(test_chatgpt_multiple_prompts())
    print("\n" + "=" * 60)
    print("✅ ChatGPT tests completed")
    print("=" * 60)
