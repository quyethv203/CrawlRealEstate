import asyncio
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler

from .base_auth_strategy import BaseAuthStrategy


class BatDongSanAuthStrategy(BaseAuthStrategy):
    """Authentication strategy for batdongsan.com.vn - popup based login"""

    async def login(self, crawler: AsyncWebCrawler, username: str, password: str) -> bool:
        """Perform popup login to BatDongSan (based on successful test)"""
        try:
            self.logger.info(f"Starting BatDongSan login for user: {username}")

            # Step 1: Navigate to homepage
            result = await crawler.arun(url="https://batdongsan.com.vn")
            if not result.success:
                self.logger.error("Failed to load BatDongSan homepage")
                return False

            self.logger.info("Homepage loaded successfully")

            # Step 2: Execute login script (proven to work)
            login_script = f"""
            async function batdongSanLogin() {{
                try {{
                    console.log('Starting BatDongSan login process...');

                    // Wait for page load
                    await new Promise(resolve => setTimeout(resolve, 3000));

                    // Find login button
                    let loginBtn = document.querySelector('a[href*="dang-nhap"]') ||
                                  document.querySelector('.btn-login') ||
                                  document.querySelector('.login-link') ||
                                  document.querySelector('.header-login');

                    // Fallback: find by text content
                    if (!loginBtn) {{
                        const links = document.querySelectorAll('a');
                        for (const link of links) {{
                            if (link.textContent.toLowerCase().includes('đăng nhập')) {{
                                loginBtn = link;
                                break;
                            }}
                        }}
                    }}

                    if (!loginBtn) {{
                        console.log('Login button not found');
                        return {{ success: false, error: 'Login button not found' }};
                    }}

                    console.log('Found login button, clicking...');
                    loginBtn.click();

                    // Wait for popup/modal to appear
                    await new Promise(resolve => setTimeout(resolve, 4000));

                    // Find form inputs in popup
                    let emailInput = document.querySelector('input[name="Email"]') ||
                                   document.querySelector('input[name="email"]') ||
                                   document.querySelector('input[type="email"]') ||
                                   document.querySelector('#Email') ||
                                   document.querySelector('#email') ||
                                   document.querySelector('input[placeholder*="email"]');

                    let passwordInput = document.querySelector('input[name="Password"]') ||
                                      document.querySelector('input[name="password"]') ||
                                      document.querySelector('input[type="password"]') ||
                                      document.querySelector('#Password') ||
                                      document.querySelector('#password');

                    if (!emailInput || !passwordInput) {{
                        console.log('Form inputs not found in popup');
                        return {{ 
                            success: false, 
                            error: 'Form inputs not found',
                            emailFound: !!emailInput,
                            passwordFound: !!passwordInput
                        }};
                    }}

                    console.log('Found form inputs, filling credentials...');

                    // Fill credentials
                    emailInput.value = '{username}';
                    passwordInput.value = '{password}';

                    // Trigger input events
                    emailInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    emailInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    passwordInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    passwordInput.dispatchEvent(new Event('change', {{ bubbles: true }}));

                    await new Promise(resolve => setTimeout(resolve, 1500));

                    // Find and click submit button
                    let submitBtn = document.querySelector('button[type="submit"]') ||
                                  document.querySelector('.btn-login') ||
                                  document.querySelector('.btn-submit') ||
                                  document.querySelector('input[type="submit"]');

                    if (!submitBtn) {{
                        const buttons = document.querySelectorAll('button');
                        for (const btn of buttons) {{
                            if (btn.textContent.toLowerCase().includes('đăng nhập')) {{
                                submitBtn = btn;
                                break;
                            }}
                        }}
                    }}

                    if (!submitBtn) {{
                        console.log('Submit button not found');
                        return {{ success: false, error: 'Submit button not found' }};
                    }}

                    console.log('Submitting login form...');
                    submitBtn.click();

                    // Wait for login processing
                    await new Promise(resolve => setTimeout(resolve, 5000));

                    return {{ success: true, message: 'Login process completed' }};

                }} catch (error) {{
                    console.error('Login error:', error);
                    return {{ success: false, error: error.message }};
                }}
            }}

            return await batdongSanLogin();
            """

            # Execute login script
            result = await crawler.arun(
                url="https://batdongsan.com.vn",
                js_code=login_script,
                wait_for="networkidle",
                page_timeout=60000
            )

            # Wait for processing and verify
            await asyncio.sleep(5)

            is_logged_in = await self.verify_login(crawler)

            if is_logged_in:
                self.logger.info("BatDongSan login successful")
            else:
                self.logger.error("BatDongSan login failed - verification failed")

            return is_logged_in

        except Exception as e:
            self.logger.error(f"BatDongSan login failed: {e}")
            return False

    async def verify_login(self, crawler: AsyncWebCrawler) -> bool:
        """Verify login status using multiple methods"""
        try:
            # Method 1: Check homepage for user indicators
            result = await crawler.arun(url="https://batdongsan.com.vn")

            if result.success:
                soup = BeautifulSoup(result.html, 'html.parser')

                # Look for user indicators
                user_indicators = soup.select([
                    '.user-info', '.user-name', '.account-dropdown',
                    '.user-menu', 'a[href*="ca-nhan"]', 'a[href*="profile"]',
                    '.logout', '.dang-xuat', '[data-user]', '.header-user'
                ])

                # Check if login buttons are gone
                login_indicators = soup.select([
                    'a[href*="dang-nhap"]', '.btn-login', '.login-link'
                ])

                if user_indicators and not login_indicators:
                    self.logger.info("Login verified: user indicators found, login buttons gone")
                    return True

                # Method 2: Check protected page access (most reliable)
                return await self._check_protected_page_access(crawler)

            return False

        except Exception as e:
            self.logger.warning(f"Login verification failed: {e}")
            return False

    async def _check_protected_page_access(self, crawler: AsyncWebCrawler) -> bool:
        """Check if we can access protected pages (most reliable method)"""
        try:
            protected_urls = [
                "https://batdongsan.com.vn/dang-tin",
                "https://batdongsan.com.vn/ca-nhan"
            ]

            for url in protected_urls:
                result = await crawler.arun(url=url)

                if result.success:
                    # If we can access without redirect to login, we're logged in
                    if "dang-nhap" not in result.url.lower():
                        self.logger.info(f"Login verified via protected page access: {url}")
                        return True
                    else:
                        self.logger.info(f"Redirected to login from {url} - not logged in")
                        return False

            return False

        except Exception as e:
            self.logger.warning(f"Protected page check failed: {e}")
            return False

    def get_phone_selectors(self) -> list:
        """Get CSS selectors for phone extraction after login"""
        return [
            '.re__contact-phone',
            '.contact-phone',
            '.phone-number',
            '[data-phone]',
            '.seller-phone',
            '.contact-item .phone',
            '.seller-contact .phone',
            '.re__contact-item .phone'
        ]