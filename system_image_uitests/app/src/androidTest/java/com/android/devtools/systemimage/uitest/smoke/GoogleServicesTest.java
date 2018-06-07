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

import android.app.Instrumentation;
import android.support.test.runner.AndroidJUnit4;
import android.support.test.uiautomator.UiDevice;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiScrollable;
import android.support.test.uiautomator.UiSelector;

import com.android.devtools.systemimage.uitest.annotations.TestInfo;
import com.android.devtools.systemimage.uitest.common.Res;
import com.android.devtools.systemimage.uitest.framework.SystemImageTestFramework;
import com.android.devtools.systemimage.uitest.utils.AppLauncher;
import com.android.devtools.systemimage.uitest.utils.AppManager;
import com.android.devtools.systemimage.uitest.utils.GoogleAppUtil;
import com.android.devtools.systemimage.uitest.utils.Wait;
import com.android.devtools.systemimage.uitest.watchers.AddGoogleAccountWatcher;
import com.android.devtools.systemimage.uitest.watchers.GoogleAppConfirmationWatcher;

import org.junit.Rule;
import org.junit.Test;
import org.junit.runner.RunWith;

import static org.junit.Assert.assertTrue;

/**
 * Test to verify that Google services are available on Google API images
 */

@RunWith(AndroidJUnit4.class)
public class GoogleServicesTest {
    private static final String WIDGET_TEXT_VIEW_CLASS = "android.widget.TextView";

    @Rule
    public final SystemImageTestFramework testFramework = new SystemImageTestFramework();

    private int api = testFramework.getApi();

    /**
     * Verifies that Google services are available on Google API images
     * <p>
     * This is run to qualify releases. Please involve the test team in substantial changes.
     * <p>
     * TR ID: C14578827
     * <p>
     *   <pre>
     *   Test Steps:
     *   1. Start an emulator AVD targeting Google Add On image.
     *   2. Open Settings > Apps.
     *   3. From the Overflow menu, select "Show system".
     *   4. Scroll through the list.
     *   Verify:
     *   Google Play Services, Google Services Framework and Maps
     *   applications are present.
     *   </pre>
     */
    @Test
    @TestInfo(id = "14578827")
    public void verifyGoogleApps() throws Exception{
        Instrumentation instrumentation = testFramework.getInstrumentation();

        if (!testFramework.isGoogleApiImage() || !testFramework.isGoogleApiAndPlayImage()) {
            return;
        }

        AppManager.openSystemAppList(instrumentation);

        UiScrollable appList=
                new UiScrollable(new UiSelector().resourceIdMatches(Res.APPS_LIST_CONTAINER_RES));
        appList.setAsVerticalList();

        assertTrue("Cannot find Google Play services", appList.getChildByText(
                new UiSelector().className(WIDGET_TEXT_VIEW_CLASS),
                "Google Play services").exists());
        assertTrue("Cannot find Google Services Framework", appList.getChildByText(
                new UiSelector().className(WIDGET_TEXT_VIEW_CLASS),
                "Google Services Framework").exists());
        assertTrue("Cannot find Maps", appList.getChildByText(
                new UiSelector().className(WIDGET_TEXT_VIEW_CLASS),
                "Maps").exists());
    }

    /**
     * Verify the contents of the Location Settings page
     * <p>
     * This is run to qualify releases. Please involve the test team in substantial changes.
     * <p>
     * TR ID: C14578827
     * <p>
     *   <pre>
     *   Test Steps:
     *   1. Start an emulator AVD targeting Google Add On image
     *   2. Open Settings > Location
     *   Verify:
     *   Location enable toggle button
     *   Verify location Mode
     *   Verify recent location requests
     *   </pre>
     */
    @Test
    @TestInfo(id = "14578827")
    public void verifyLocationSettings() throws Exception {
        Instrumentation instrumentation = testFramework.getInstrumentation();
        UiDevice device = UiDevice.getInstance(instrumentation);

        // Open settings
        AppLauncher.launch(instrumentation, "Settings");

        // Find and click "Location" in Settings
        UiScrollable itemList =
                new UiScrollable(
                        new UiSelector().resourceIdMatches(Res.SETTINGS_LIST_CONTAINER_RES)
                );
        itemList.setAsVerticalList();
        if(api > 18) {
            if(api >= 26) {
                String securityLabel = api == 26 ? "Security & Location" : "Security & location";
                UiObject security = itemList.getChildByText(new UiSelector().className("android.widget.TextView"),
                        securityLabel);
                security.clickAndWaitForNewWindow();
            }
            UiObject location = itemList.getChildByText(new UiSelector().className(WIDGET_TEXT_VIEW_CLASS),
                            "Location");
            location.clickAndWaitForNewWindow();

            assertTrue("Cannot find location toggle button", device.findObject(
                    new UiSelector().className("android.widget.Switch")).exists());
            assertTrue("Cannot find mode", device.findObject(new UiSelector().text(
                    "Mode")).exists());
            assertTrue("Cannot find recent location", device.findObject(new UiSelector().text(
                    "Recent location requests")).exists());
        } else {
            UiObject item =
                    itemList.getChildByText(
                            new UiSelector().className(WIDGET_TEXT_VIEW_CLASS),
                            "Location access");
            item.clickAndWaitForNewWindow();

            // API specific assertion, since mode and recent location requests are absent in API 18
            assertTrue("Cannot find location toggle button", device.findObject(new
                    UiSelector().className("android.widget.Switch")).exists());
        }
    }

    /**
     * Logs the user into Google Chrome app.
     * <p>
     * This is run to qualify releases. Please involve the test team in substantial changes.
     * <p>
     * TR ID: d7f5673a-a3d0-4f50-856a-dfa10ce5c21c
     * <p>
     *   <pre>
     *   Test Steps:
     *   1. Start an emulator with API 24+ Google APIs support.
     *   2. Launch Chrome.
     *   3. Log into Chrome using the test account.
     *   4. Open the Chrome menu > Settings.
     *   5. Find logged user name.
     *   6. Log user out of Chrome.
     *   Verify:
     *   1. Logged in user name is present.
     *   2. Log in user prompt or user promo is present.
     *   </pre>
     */
    @Test
    @TestInfo(id = "d7f5673a-a3d0-4f50-856a-dfa10ce5c21c")
    public void loginGoogleChrome() throws Exception {
        Instrumentation instrumentation = testFramework.getInstrumentation();
        final UiDevice device = UiDevice.getInstance(instrumentation);

        if (api < 24) {
            return;
        }

        final String username = "David Play";

        AppLauncher.launch(instrumentation, "Chrome");
        new AddGoogleAccountWatcher(device).checkForCondition();

        signInToChrome(instrumentation);

        final UiObject chromeUpdateButton = device.findObject(
                new UiSelector().resourceId(Res.CHROME_MENU_BADGE_RES)
        );

        if (new Wait().until(new Wait.ExpectedCondition() {
                    @Override
                    public boolean isTrue() {
                        return chromeUpdateButton.exists();
                }})) {
            chromeUpdateButton.clickAndWaitForNewWindow();
        }

        final UiObject chromeMenuButton = device.findObject(
                new UiSelector().resourceId(Res.CHROME_MENU_BUTTON_RES));

        if (new Wait().until(new Wait.ExpectedCondition() {
                    @Override
                    public boolean isTrue() {
                        return chromeMenuButton.exists();
                }})) {
            chromeMenuButton.clickAndWaitForNewWindow();
        }

        final UiObject settingsButton = device.findObject(new UiSelector().text("Settings"));

        if (new Wait().until(new Wait.ExpectedCondition() {
            @Override
            public boolean isTrue() {
                return settingsButton.exists();
            }})) {
            settingsButton.clickAndWaitForNewWindow();
        }

        final UiObject signInPromoButton = device.findObject(
                new UiSelector().resourceId(Res.CHROME_SIGNIN_PROMO_RES));

        if (new Wait().until(new Wait.ExpectedCondition() {
            @Override
            public boolean isTrue() {
                return signInPromoButton.exists();
            }})) {
            signInPromoButton.clickAndWaitForNewWindow();
        }

        final UiObject signInLabel = device.findObject(new UiSelector().text("Sign in to Chrome"));

        if (new Wait().until(new Wait.ExpectedCondition() {
            @Override
            public boolean isTrue() {
                return signInLabel.exists();
            }})) {
            signInLabel.clickAndWaitForNewWindow();
        }

        signInToChrome(instrumentation);

        final UiObject signedInLabel = device.findObject(new UiSelector().text(username));

        assertTrue("Google log in was unsuccessful", new Wait().
                until(new Wait.ExpectedCondition() {
                    @Override
                    public boolean isTrue() {
                        return signedInLabel.exists();
                    }})
        );
        signedInLabel.clickAndWaitForNewWindow();
        final UiObject signOutLabel = device.findObject(new UiSelector().text("Sign out of Chrome"));

        if (new Wait().until(new Wait.ExpectedCondition() {
            @Override
            public boolean isTrue() {
                return signOutLabel.exists();
            }})) {
            signOutLabel.clickAndWaitForNewWindow();
        }

        final UiObject signOutButton = device.findObject(new UiSelector().text("SIGN OUT"));

        if (new Wait().until(new Wait.ExpectedCondition() {
            @Override
            public boolean isTrue() {
                return signOutButton.exists();
            }})) {
            signOutButton.clickAndWaitForNewWindow();
        }

        final UiObject signInPromoCloseButton = device.findObject(
                new UiSelector().resourceId(Res.CHROME_SIGNIN_PROMO_CLOSE_RES));

        if (new Wait().until(new Wait.ExpectedCondition() {
            @Override
            public boolean isTrue() {
                return signInPromoCloseButton.exists();
            }})) {
            signInPromoCloseButton.clickAndWaitForNewWindow();
        }

        assertTrue("Google log out was unsuccessful", new Wait().
                until(new Wait.ExpectedCondition() {
                    @Override
                    public boolean isTrue() {
                        return signInLabel.exists() || signInPromoCloseButton.exists();
                    }}));
        if (signInLabel.exists()) {
            signInLabel.click();
        } else {
            signInPromoCloseButton.click();
        }
    }

    /**
     * Logs into Chrome if the Sign In button is presented
     */
    private void signInToChrome(Instrumentation instrumentation) throws Exception {
        final UiDevice device = UiDevice.getInstance(instrumentation);
        final UiObject signInButton = device.findObject(new UiSelector().text("SIGN IN"));
        boolean hasSignInButton = new Wait(5L).until(new Wait.ExpectedCondition() {
            @Override
            public boolean isTrue() {
                return signInButton.exists();
            }
        });

        if (hasSignInButton) {
            signInButton.clickAndWaitForNewWindow();
            GoogleAppUtil.loginGoogleApp(instrumentation);
            AppLauncher.launch(instrumentation, "Chrome");
            new GoogleAppConfirmationWatcher(device).checkForCondition();
        }

        final UiObject moreButton = device.findObject(
                new UiSelector().resourceId(Res.CHROME_MORE_BUTTON_RES));

        if (new Wait().until(new Wait.ExpectedCondition() {
            @Override
            public boolean isTrue() {
                return moreButton.exists();
            }})) {
            moreButton.clickAndWaitForNewWindow();
        }

        final UiObject continueButton = device.findObject(new UiSelector().text("CONTINUE"));

        if (new Wait().until(new Wait.ExpectedCondition() {
            @Override
            public boolean isTrue() {
                return continueButton.exists();
            }})) {
            continueButton.clickAndWaitForNewWindow();
        }

        final UiObject gotItButton = device.findObject(new UiSelector().text("OK, GOT IT"));

        if (new Wait().until(new Wait.ExpectedCondition() {
            @Override
            public boolean isTrue() {
                return gotItButton.exists();
            }})) {
            gotItButton.clickAndWaitForNewWindow();
        }
    }
}
