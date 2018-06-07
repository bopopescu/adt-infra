/*
 * Copyright (c) 2016 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.android.devtools.systemimage.uitest.smoke;

import com.android.devtools.systemimage.uitest.annotations.TestInfo;
import com.android.devtools.systemimage.uitest.common.Res;
import com.android.devtools.systemimage.uitest.framework.SystemImageTestFramework;
import com.android.devtools.systemimage.uitest.utils.AppLauncher;
import com.android.devtools.systemimage.uitest.utils.PackageInstallationUtil;
import com.android.devtools.systemimage.uitest.utils.Wait;
import com.android.devtools.systemimage.uitest.watchers.AppWatcher;

import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.Timeout;
import org.junit.runner.RunWith;

import android.app.Instrumentation;
import android.support.test.runner.AndroidJUnit4;
import android.support.test.uiautomator.By;
import android.support.test.uiautomator.UiDevice;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiObjectNotFoundException;
import android.support.test.uiautomator.UiSelector;
import android.support.test.uiautomator.Until;
import android.util.Log;

import java.util.concurrent.TimeUnit;

import static org.junit.Assert.assertTrue;

/**
 * Test for app interactions.
 */
@RunWith(AndroidJUnit4.class)
public class AppTest {
    @Rule
    public final SystemImageTestFramework testFramework = new SystemImageTestFramework();

    @Rule
    public Timeout globalTimeout = Timeout.seconds(240);

    private int api = testFramework.getApi();
    private final String TAG = "AppTest";

    /**
     * Verifies an app runs on the emulator.
     * <p/>
     * The test installs, launches, and uninstalls the app.
     * <p/>
     * This is run to qualify releases. Please involve the test team in substantial changes.
     * <p/>
     * TR ID: C14578823
     * <p/>
     *   <pre>
     *   Test Steps:
     *   1. Start the emulator.
     *   2. Install HelloComputer app.
     *   3. Open the app.
     *   Verify:
     *   App runs on the emulator. Image of a leaf is displayed on the emulator.
     *   </pre>
     * <p/>
     * This test does not run on API 18 due to RsHelloCompute app crashing on API 18.
     */
    @Test
    @TestInfo(id = "14578823")
    public void installAppAndLaunch() throws Exception {
        Instrumentation instrumentation = testFramework.getInstrumentation();

        // Disable test for API 18. Enable when bug 30437951 is fixed.
        if (api == 18) {
            return;
        }

        // Install RsHelloCompute, if not already present.
        if (!PackageInstallationUtil.isPackageInstalled(instrumentation,
                "com.example.android.rs.hellocompute")) {
            PackageInstallationUtil.installApk(instrumentation, "HelloCompute.apk");
        }

        AppLauncher.launch(instrumentation, "RsHelloCompute");
        assertTrue(testFramework.getDevice().findObject(new UiSelector().resourceId(
                Res.APP_IMAGE_VIEW_ID)).exists());
    }

    /**
     * Verify website is bookmarked.
     * <p/>
     * This is run to qualify releases. Please involve the test team in substantial changes.
     * <p/>
     * TR ID: C14578831
     * <p/>
     *   <pre>
     *   (Note: Test varies for API 24 and above, because it uses the Chrome browser app.)
     *   1. Launch emulator.
     *   2. Open Browser app.
     *   3. Tap on the address bar and enter espn.com
     *   4. Open menu (3 vertical dots).
     *   5. Tap on "Save to bookmarks" and tap OK.
     *   6. Assert message that bookmark is added.
     *   7. Open menu (3 vertical dots).
     *   8. Tap on "Bookmarks"
     *   Verify:
     *   Website is bookmarked.
     *   </pre>
     */
    @Test
    @TestInfo(id = "14578831")
    public void bookmarkWebSiteInBrowser() throws Exception {
        Instrumentation instrumentation = testFramework.getInstrumentation();
        final UiDevice device = UiDevice.getInstance(instrumentation);

        if (api >= 24 && (testFramework.isGoogleApiImage() || testFramework.isGoogleApiAndPlayImage())) {
            AppLauncher.launch(instrumentation, "Chrome");

            // If this is the first launch, dismiss the "Welcome to Chrome" screen.
            UiObject welcomeScreen = device.findObject(
                    new UiSelector().text("Welcome to Chrome"));
            if (welcomeScreen.waitForExists(TimeUnit.SECONDS.toMillis(3))) {
                device.findObject(
                        new UiSelector().resourceId(Res.CHROME_TERMS_ACCEPT_BUTTON_RES))
                        .clickAndWaitForNewWindow();
            }

            // Dismiss the "Sign in to Chrome" screen if it's there.
            UiObject noThanksButton = device.findObject(
                    new UiSelector().resourceIdMatches(Res.CHROME_NO_THANKS_BUTTON_RES));
            if (noThanksButton.waitForExists(TimeUnit.SECONDS.toMillis(3))) {
                noThanksButton.clickAndWaitForNewWindow();
            }

            // Click the search box if it's there.
            UiObject searchBox = device.findObject(new UiSelector().resourceId(
                    Res.CHROME_SEARCH_BOX_RES));
            if (searchBox.waitForExists(TimeUnit.SECONDS.toMillis(3))) {
                searchBox.clickAndWaitForNewWindow();
            }

            new AppWatcher(device).checkForCondition();

            UiObject textField = device.findObject(
                    new UiSelector().resourceId(Res.CHROME_URL_BAR_RES));

            textField.click();
            textField.clearTextField();
            // Include a timestamp in the URL so it's not already bookmarked. (On Chrome, the UI
            // changes in that case.)
            textField.setText("http://espn.com");
            device.pressEnter();
            device.pressMenu();

            boolean notBookmarked = new Wait().until(new Wait.ExpectedCondition() {
                @Override
                public boolean isTrue() throws UiObjectNotFoundException {
                    return device.findObject(new UiSelector().description("Bookmark this page")).exists();
                }
            });
            if (notBookmarked) {
                device.findObject(new UiSelector().description("Bookmark this page")).click();
                new AppWatcher(device).checkForCondition();
                device.pressMenu();
            }
            // After bookmarking, the button description changes.
            assertTrue("Bookmark was not set",
                    device.findObject(new UiSelector().description("Edit bookmark")).exists());
            // Verify the new bookmark is in the list.
            UiObject bookmarks = device.findObject(new UiSelector().text("Bookmarks"));
            bookmarks.waitForExists(TimeUnit.SECONDS.toMillis(5));
            if (bookmarks.exists()) {
                bookmarks.clickAndWaitForNewWindow();
            }

            Log.d(TAG, "The bookmark is set");
            new AppWatcher(device).checkForCondition();

            UiObject mobileBookmarks = device.findObject(new UiSelector().text("Mobile bookmarks")
                    .resourceId(Res.CHROME_TITLE_RES));
            mobileBookmarks.waitForExists(TimeUnit.SECONDS.toMillis(5));
            if (mobileBookmarks.exists()) {
                mobileBookmarks.clickAndWaitForNewWindow();
            }

            Log.d(TAG, "Searching for bookmark...");
            new AppWatcher(device).checkForCondition();

            assertTrue("Cannot find bookmark",
                    new Wait().until(new Wait.ExpectedCondition() {
                        @Override
                        public boolean isTrue() {
                            return device.findObject(
                                    new UiSelector().textContains(("kmarks"))).exists() &&
                                    device.findObject(new UiSelector().textContains("ESPN").resourceId(
                                            Res.CHROME_TITLE_RES)).exists();
                        }
                    })
            );

            device.findObject(new UiSelector().resourceId(
                    Res.CHROME_CLOSE_MENU_BUTTON_RES)).clickAndWaitForNewWindow();

            Log.d(TAG, "Closing the menu");

            // Delete the bookmark.
            device.pressMenu();
            device.findObject(
                    new UiSelector().description("Edit bookmark")).clickAndWaitForNewWindow();
            device.findObject(new UiSelector().description("Delete bookmarks")).click();

        } else if (api == 24) {
            // API 24 uses WebView Browser as the default browser. Does not have bookmarking
            // options.
            return;
        } else {
            AppLauncher.launch(instrumentation, "Browser");
            UiObject textField = device.findObject(
                    new UiSelector().resourceId(Res.BROWSER_URL_TEXT_FIELD_RES));
            textField.click();
            textField.clearTextField();
            textField.setText("espn.com");
            device.pressEnter();
            device.pressMenu();
            device.findObject(new UiSelector().text("Save to bookmarks")).click();
            device.findObject(new UiSelector().text("OK")).click();
            device.pressMenu();
            UiObject bookmarks = device.findObject(new UiSelector().text("Bookmarks"));
            bookmarks.waitForExists(TimeUnit.SECONDS.toMillis(5));
            bookmarks.click();
            boolean hasBookmarks = device.wait(
                    Until.hasObject(By.text("Bookmarks")),
                    TimeUnit.MILLISECONDS.convert(3L, TimeUnit.SECONDS)
            );
            boolean hasNewBookmark = device.wait(
                    Until.hasObject(By.res(Res.BROWSER_BOOKMARKS_LABEL_RES)),
                    TimeUnit.MILLISECONDS.convert(3L, TimeUnit.SECONDS)
            );
            assertTrue("Cannot find ESPN bookmark",
                    hasBookmarks && hasNewBookmark);
            device.findObject(new UiSelector().textContains(
                    "ESPN").resourceId(Res.BROWSER_BOOKMARKS_LABEL_RES)).swipeUp(400);
            // Delete the bookmark.
            device.findObject(new UiSelector().text("Delete bookmark")).clickAndWaitForNewWindow();
            device.findObject(new UiSelector().text("OK")).clickAndWaitForNewWindow();
        }
    }

    /**
     * Verify bookmarked website is set as the home page.
     * <p/>
     * This is run to qualify releases. Please involve the test team in substantial changes.
     * <p/>
     * TT ID: 8649851d-da41-45f8-8e73-82b98ea418d0
     * <p/>
     *   <pre>
     *   (Note: Test currently supports APIs 23 and below.
     *   Does not work on Chrome, which is used in later APIs.)
     *   1. Launch emulator.
     *   2. Open Browser app.
     *   3. Tap on the address bar and enter espn.com
     *   4. Open menu (3 vertical dots).
     *   5. Go to Settings > General > Set Homepage.
     *   6. Select Other.
     *   7. Set Homepage to new target website.
     *   8. Relaunch browser.
     *   Verify:
     *   The selected website is correctly set as browser home page.
     *   </pre>
     */
    @Test
    @TestInfo(id = "8649851d-da41-45f8-8e73-82b98ea418d0")
    public void setHomePageInBrowser() throws Exception {
        Instrumentation instrumentation = testFramework.getInstrumentation();
        final UiDevice device = UiDevice.getInstance(instrumentation);
        String homepage = "espn.com";
        String appName = "Browser";

        if (api >= 17 && api <= 23) {
            AppLauncher.launch(instrumentation, appName);
            setHomePage(device, "Other", "http://" + homepage);
            device.pressHome();

            AppLauncher.launch(instrumentation, appName);
            device.findObject(new UiSelector().resourceId(Res.BROWSER_TAB_SWITCHER_RES))
                    .clickAndWaitForNewWindow();
            device.findObject(new UiSelector().resourceId(Res.BROWSER_CLOSE_TAB_RES))
                    .clickAndWaitForNewWindow();
            device.pressHome();

            AppLauncher.launch(instrumentation, appName);
            UiObject urlField = device.findObject(
                    new UiSelector().resourceId(Res.BROWSER_URL_TEXT_FIELD_RES));
            urlField.waitForExists(TimeUnit.SECONDS.toMillis(5));

            assertTrue("Homepage not set correctly",
                    urlField.exists() && urlField.getText().contains(homepage));

            device.pressHome();
            AppLauncher.launch(instrumentation, appName);
            setHomePage(device, "Default page");
        }
    }

    /**
     * Helper method to set a homepage.  Homepage vararg optionally takes 2 arguments,
     * the homepage type (ie. "Other", "Default page", etc.), and the target website url.
     * Note that a selection of "Default page" would not require a url to be given.
     */
    private void setHomePage(UiDevice device, String ...homepage) throws Exception {
        device.pressMenu();

        UiObject settings = device.findObject(new UiSelector().text("Settings"));
        settings.waitForExists(TimeUnit.SECONDS.toMillis(5));
        settings.clickAndWaitForNewWindow();

        UiObject general = device.findObject(new UiSelector().text("General"));
        general.waitForExists(TimeUnit.SECONDS.toMillis(5));
        general.clickAndWaitForNewWindow();

        UiObject setHomepage = device.findObject(new UiSelector().text("Set homepage"));
        setHomepage.waitForExists(TimeUnit.SECONDS.toMillis(5));
        setHomepage.clickAndWaitForNewWindow();

        UiObject type = device.findObject(new UiSelector().text(homepage[0]));
        type.waitForExists(TimeUnit.SECONDS.toMillis(5));
        type.clickAndWaitForNewWindow();

        if (homepage.length > 1) {
            UiObject textField = device.findObject(
                    new UiSelector().className("android.widget.EditText").
                            packageName("com.android.browser"));
            textField.click();
            textField.clearTextField();
            textField.setText(homepage[1]);

            UiObject ok = device.findObject(new UiSelector().text("OK"));
            ok.waitForExists(TimeUnit.SECONDS.toMillis(5));
            ok.clickAndWaitForNewWindow();
        }
    }
}
