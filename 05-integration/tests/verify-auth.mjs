import assert from "node:assert/strict";
import { chromium } from "playwright";

const site = "http://localhost:3000";
const email = "aigerim@example.com";
const browser = await chromium.launch({ channel: process.env.BROWSER_CHANNEL });

try {
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto(`${site}/account`);
  await page.waitForURL(`${site}/login`);
  console.log("PASS guest redirected to login");

  await page.getByLabel("E-mail").fill(email);
  await page.getByLabel("Password").fill("wrong-password");
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await page.getByRole("alert").filter({ hasText: "Invalid e-mail or password" }).waitFor();
  assert.equal(await page.getByLabel("E-mail").inputValue(), email);
  assert.equal(await page.getByLabel("Password").inputValue(), "");
  console.log("PASS failed login keeps email and clears password");

  await page.getByLabel("Password").fill("aigerim-demo-pass");
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await page.waitForURL(`${site}/account`);
  await page.getByText(email, { exact: true }).waitFor();
  await page.getByText("student", { exact: true }).waitFor();
  const cookie = (await context.cookies(site)).find(({ name }) => name === "session");
  assert.ok(cookie);
  assert.equal(cookie.httpOnly, true);
  assert.equal(cookie.secure, true);
  assert.equal(cookie.sameSite, "Lax");
  assert.equal(cookie.path, "/");
  const remaining = cookie.expires - Date.now() / 1000;
  assert.ok(remaining >= 890 && remaining <= 901);
  assert.equal(await page.evaluate(() => document.cookie), "");
  assert.equal(await page.locator("html").innerHTML().then((html) => html.includes(cookie.value)), false);
  console.log("PASS account and session flags HttpOnly, Secure, SameSite=Lax, Path=/, Max-Age≈900, document.cookie empty");

  await page.goto(`${site}/courses/ai-integration`);
  assert.equal(await page.getByLabel("Student ID").count(), 0);
  await page.getByRole("button", { name: "Enroll", exact: true }).click();
  await page.getByRole("alert").filter({ hasText: "This student is already enrolled." }).waitFor();
  console.log("PASS the course form uses the authenticated student's profile");

  for (const route of ["my-courses", "my-courses-rest"]) {
    await page.goto(`${site}/${route}`);
    await page.getByRole("heading", { name: "My courses: Daniyar Bekov" }).waitFor();
    assert.equal(await page.locator("main li").count(), 3);
  }
  console.log("PASS Lab 8 comparison pages still show three courses each");

  await page.goto(`${site}/account`);
  await page.getByRole("button", { name: "Log out" }).click();
  await page.waitForURL(`${site}/login`);
  assert.equal((await context.cookies(site)).some(({ name }) => name === "session"), false);
  await page.goto(`${site}/account`);
  await page.waitForURL(`${site}/login`);
  console.log("PASS logout removes the cookie and the account requires a session again");

  await context.addCookies([{ name: "session", value: "invalid-session", url: site, httpOnly: true }]);
  await page.goto(`${site}/account`);
  await page.waitForURL(`${site}/login`);
  assert.equal(await page.getByText(email, { exact: true }).count(), 0);
  console.log("PASS malformed session cookie is denied by the API-backed check");
} finally {
  await browser.close();
}
