import asyncio
import base64
from playwright.async_api import async_playwright


async def capture_screenshot(url: str) -> dict:
    """
    Captures high-quality screenshots for phishing analysis.

    Improvements:
    1. Better desktop rendering
    2. More stable page loading
    3. Cookie popup handling
    4. Improved JS-heavy website support
    5. Better redirect screenshot capture
    6. More reliable screenshot quality for LLaVA
    """

    if not url.startswith("http"):
        url = "http://" + url

    redirect_chain = []
    redirect_screenshots = []
    final_url = url

    try:
        async with async_playwright() as p:

            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-blink-features=AutomationControlled"
                ]
            )

            
            context = await browser.new_context(
                viewport={"width": 1440, "height": 2200},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                java_script_enabled=True,
                ignore_https_errors=True
            )

            page = await context.new_page()

           
            async def on_response(response):
                if response.status in [301, 302, 303, 307, 308]:
                    redirect_chain.append({
                        "from": response.url,
                        "status": response.status,
                        "to": response.headers.get("location", "")
                    })

            page.on("response", on_response)

          
            try:
                await page.goto(
                    url,
                    wait_until="networkidle",
                    timeout=25000
                )

            except Exception:

                try:
                    await page.goto(
                        url,
                        wait_until="load",
                        timeout=20000
                    )

                except Exception:

                    try:
                        await page.goto(
                            url,
                            wait_until="domcontentloaded",
                            timeout=15000
                        )

                    except Exception:

                        await browser.close()

                        return {
                            "screenshot_base64": None,
                            "redirect_screenshots": [],
                            "final_url": url,
                            "redirect_chain": [],
                            "has_redirect": False,
                            "error": "Page failed to load"
                        }

            try:
                await page.wait_for_timeout(3000)
            except Exception:
                pass

            popup_selectors = [
                "button:has-text('Accept')",
                "button:has-text('I Agree')",
                "button:has-text('Allow')",
                "button:has-text('Accept All')",
                "button:has-text('Continue')",
                "button:has-text('OK')",
                "[aria-label='Accept']"
            ]

            for selector in popup_selectors:
                try:
                    await page.click(selector, timeout=1500)
                    await page.wait_for_timeout(500)
                except Exception:
                    pass

           
            try:
                await page.bring_to_front()
            except Exception:
                pass

            final_url = page.url

           
            screenshot_bytes = await page.screenshot(
                full_page=False
            )

            screenshot_b64 = base64.b64encode(
                screenshot_bytes
            ).decode("utf-8")

           
            if redirect_chain:

                for hop in redirect_chain[:3]:

                    hop_url = hop.get("to", "")

                    if not hop_url or not hop_url.startswith("http"):
                        continue

                    try:
                        hop_page = await context.new_page()

                        await hop_page.goto(
                            hop_url,
                            wait_until="networkidle",
                            timeout=15000
                        )

                        await hop_page.wait_for_timeout(1500)

                        hop_bytes = await hop_page.screenshot(
                            full_page=False
                        )

                        redirect_screenshots.append({
                            "url": hop_url,
                            "screenshot_base64": base64.b64encode(
                                hop_bytes
                            ).decode("utf-8")
                        })

                        await hop_page.close()

                    except Exception:
                        pass

            await browser.close()

            has_redirect = (
                final_url.rstrip("/") != url.rstrip("/")
            )

            return {
                "screenshot_base64": screenshot_b64,
                "redirect_screenshots": redirect_screenshots,
                "final_url": final_url,
                "redirect_chain": [
                    r.get("from", "")
                    for r in redirect_chain
                ],
                "redirect_chain_detail": redirect_chain,
                "has_redirect": has_redirect,
                "error": None
            }

    except Exception as e:

        return {
            "screenshot_base64": None,
            "redirect_screenshots": [],
            "final_url": url,
            "redirect_chain": [],
            "has_redirect": False,
            "error": str(e)
        }


def capture_screenshot_sync(url: str) -> dict:
    """
    Synchronous wrapper
    """
    return asyncio.run(capture_screenshot(url))