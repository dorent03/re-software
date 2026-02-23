/**
 * Manual Test Script for Registration and Login Flow
 * 
 * This script uses Playwright to test the registration and login functionality.
 * 
 * To run this test:
 * 1. Install Playwright: npm install -D @playwright/test
 * 2. Run: node test-registration-login.js
 * 
 * Or you can follow these manual steps in your browser:
 */

const { chromium } = require('playwright');

async function testRegistrationAndLogin() {
  console.log('Starting browser automation test...\n');
  
  // Launch browser
  const browser = await chromium.launch({ headless: false, slowMo: 500 });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // ========== REGISTRATION TEST ==========
    console.log('Step 1: Navigating to registration page...');
    await page.goto('http://localhost:3001/register');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/01-registration-page.png' });
    console.log('✓ Registration page loaded\n');

    console.log('Step 2: Filling in registration form...');
    await page.fill('#first_name', 'Test');
    await page.fill('#last_name', 'Benutzer');
    await page.fill('#reg_email', 'testbrowser@example.com');
    await page.fill('#company_name', 'TestFirma GmbH');
    await page.fill('#company_street', 'Teststraße 1');
    await page.fill('#company_zip', '10115');
    await page.fill('#company_city', 'Berlin');
    await page.fill('#reg_password', 'Test1234!');
    await page.fill('#confirm_password', 'Test1234!');
    console.log('✓ Form filled with test data\n');

    console.log('Step 3: Clicking Registrieren button...');
    await page.click('button[type="submit"]');
    
    console.log('Step 4: Waiting 3 seconds...');
    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'screenshots/02-after-registration.png' });
    
    // Check if redirected to login or if error appeared
    const currentUrl = page.url();
    const errorMessage = await page.locator('.bg-red-50').textContent().catch(() => null);
    
    console.log('\n========== REGISTRATION RESULT ==========');
    console.log('Current URL:', currentUrl);
    
    if (errorMessage) {
      console.log('❌ Error appeared:', errorMessage);
      console.log('Registration failed - see screenshot at: screenshots/02-after-registration.png\n');
    } else if (currentUrl.includes('/login')) {
      console.log('✓ SUCCESS: Redirected to login page!');
      console.log('Registration completed successfully\n');
    } else {
      console.log('⚠ Still on registration page:', currentUrl);
      console.log('Check screenshot at: screenshots/02-after-registration.png\n');
    }

    // ========== LOGIN TEST ==========
    console.log('\n========== STARTING LOGIN TEST ==========');
    console.log('Step 6: Navigating to login page...');
    await page.goto('http://localhost:3001/login');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/03-login-page.png' });
    console.log('✓ Login page loaded\n');

    console.log('Step 7: Filling in login credentials...');
    await page.fill('input[type="email"]', 'testbrowser@example.com');
    await page.fill('input[type="password"]', 'Test1234!');
    console.log('✓ Credentials entered\n');

    console.log('Step 8: Clicking Anmelden button...');
    await page.click('button[type="submit"]');
    
    console.log('Step 9: Waiting 3 seconds...');
    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'screenshots/04-after-login.png' });
    
    // Check login result
    const loginUrl = page.url();
    const loginError = await page.locator('.bg-red-50').textContent().catch(() => null);
    
    console.log('\n========== LOGIN RESULT ==========');
    console.log('Current URL:', loginUrl);
    
    if (loginError) {
      console.log('❌ Error appeared:', loginError);
      console.log('Login failed - see screenshot at: screenshots/04-after-login.png');
    } else if (loginUrl.includes('/login')) {
      console.log('⚠ Still on login page');
      console.log('Login may have failed - see screenshot at: screenshots/04-after-login.png');
    } else {
      console.log('✓ SUCCESS: Redirected from login page!');
      console.log('Likely redirected to:', loginUrl);
      
      // Try to capture visible content
      const pageTitle = await page.title();
      const h1Text = await page.locator('h1').first().textContent().catch(() => 'N/A');
      
      console.log('\nDashboard Content:');
      console.log('- Page Title:', pageTitle);
      console.log('- Main Heading:', h1Text);
      console.log('- Screenshot saved at: screenshots/04-after-login.png');
      
      // Try to find navigation or key elements
      const navLinks = await page.locator('nav a').allTextContents().catch(() => []);
      if (navLinks.length > 0) {
        console.log('- Navigation items:', navLinks.join(', '));
      }
    }

    console.log('\n========== TEST COMPLETE ==========');
    console.log('All screenshots saved in screenshots/ folder');
    
    // Keep browser open for 5 seconds so you can see the result
    await page.waitForTimeout(5000);

  } catch (error) {
    console.error('\n❌ Test failed with error:', error.message);
    await page.screenshot({ path: 'screenshots/error.png' });
  } finally {
    await browser.close();
  }
}

// Run the test
testRegistrationAndLogin().catch(console.error);
