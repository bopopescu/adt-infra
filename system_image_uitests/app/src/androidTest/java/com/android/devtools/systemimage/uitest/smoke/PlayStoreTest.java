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
import android.support.test.uiautomator.UiObjectNotFoundException;
import android.support.test.uiautomator.UiScrollable;
import android.support.test.uiautomator.UiSelector;

import com.android.devtools.systemimage.uitest.annotations.TestInfo;
import com.android.devtools.systemimage.uitest.common.Res;
import com.android.devtools.systemimage.uitest.framework.SystemImageTestFramework;
import com.android.devtools.systemimage.uitest.utils.AppLauncher;
import com.android.devtools.systemimage.uitest.utils.PlayStoreUtil;
import com.android.devtools.systemimage.uitest.utils.Wait;
import com.android.devtools.systemimage.uitest.watchers.GoogleAppConfirmationWatcher;
import com.android.devtools.systemimage.uitest.watchers.PlayStoreControlsWatcher;

import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.Timeout;
import org.junit.runner.RunWith;

import java.util.concurrent.TimeUnit;

import static org.junit.Assert.assertTrue;

/**
 * Test to verify that Google services are available on Google API images
 */

@RunWith(AndroidJUnit4.class)
public class PlayStoreTest {
    @Rule
    public final SystemImageTestFramework testFramework = new SystemImageTestFramework();

    @Rule
    public Timeout globalTimeout = Timeout.seconds(360);

    private final boolean hasGooglePlay = testFramework.getApi() >= 24 &&
            testFramework.isGoogleApiAndPlayImage();

    /**
     * Verify apps can be searched through Play Store search bar.
     * <p>
     * TT ID: 50027a89-8043-44d7-b7ed-33c631903910
     * <p>
     *   <pre>
     *   Test Steps:
     *   1. Start an emulator and launch home screen.
     *   2. Open Apps.
     *   3. Confirm that Play Store is present, then launch.
     *   4. Search for an app name on the main Play Store screen.
     *   Verify:
     *      1. Confirm that app name displays the search string.
     *   </pre>
     */

    @Test
    @TestInfo(id = "50027a89-8043-44d7-b7ed-33c631903910")
    public void testPlaySearch() throws Exception {
        Instrumentation instrumentation = testFramework.getInstrumentation();
        final UiDevice device = UiDevice.getInstance(instrumentation);
        final String application = "Messenger";

        if (hasGooglePlay) {
            boolean playStoreInstalled = PlayStoreUtil.isPlayStoreInstalled(instrumentation);

            if (playStoreInstalled) {
                PlayStoreUtil.loginGooglePlay(instrumentation);
                assertTrue("Application not found in search.",
                        hasTestApp(instrumentation, application));
                PlayStoreUtil.resetPlayStore(instrumentation);
                device.pressHome();
            }
        }
    }

    /**
     * Verify that Google Play can install and uninstall a free app on the device.
     * <p>
     * TT ID: cb0ccd97-f045-42fa-8293-a32e94e838aa
     * <p>
     *   <pre>
     *   Test Steps:
     *   1. Start an emulator and launch home screen.
     *   2. Open Apps drawer.
     *   3. Confirm that Play Store is present, then launch.
     *   4. Search for free app in store.
     *   5. If app is available for install, begin installation.
     *   6. Uninstall the app.
     *   Verify:
     *      1a. If Install button was displayed, allow installation to complete then
     *      confirm that the Open button to launch the app is present.
     *      1b. If Install button was not displayed, confirm that the Open button to
     *      launch the app is present.
     *      2. Confirm that the app was subsequently uninstalled.
     *   </pre>
     */

    @Test
    @TestInfo(id = "cb0ccd97-f045-42fa-8293-a32e94e838aa")
    public void testAppInstallation() throws Exception {
        Instrumentation instrumentation = testFramework.getInstrumentation();
        final UiDevice device = UiDevice.getInstance(instrumentation);
        final String application = "Google Translate";

        if (hasGooglePlay) {
            boolean playStoreInstalled = PlayStoreUtil.isPlayStoreInstalled(instrumentation);

            if (playStoreInstalled) {
                PlayStoreUtil.loginGooglePlay(instrumentation);
                selectApplication(instrumentation, application);
                new GoogleAppConfirmationWatcher(device).checkForCondition();

                assertTrue("Unable to install the application from Google Play",
                        PlayStoreUtil.installApplication(instrumentation));

                AppLauncher.launch(instrumentation, "Play Store");
                assertTrue("Unable to uninstall the application from Google Play",
                        PlayStoreUtil.uninstallApplication(instrumentation));

                PlayStoreUtil.resetPlayStore(instrumentation);
                device.pressHome();
            }
        }
    }

    /**
     * Verify that Google Play can install and launch an app, then uninstall the app on the device.
     * <p>
     * TT ID: 924a0428-4e07-4794-b6a7-2c9d407204aa
     * <p>
     *   <pre>
     *   Test Steps:
     *   1. Start an emulator and launch home screen.
     *   2. Open Apps.
     *   3. Confirm that Play Store is present, then launch.
     *   5. Search for free app in store.
     *   6. If app is available for install, begin installation.
     *   7. Launch the application.
     *   8. Close and uninstall the app.
     *   Verify:
     *      1a. If Install button was displayed, allow installation to complete then
     *      confirm that the Open button to launch the app is present.
     *      1b. If Install button was not displayed, confirm that the Open button to
     *      launch the app is present.
     *      2. Confirm that application launch was successful.
     *      3. Confirm that the app was subsequently uninstalled.
     *   </pre>
     */

    @Test
    @TestInfo(id = "924a0428-4e07-4794-b6a7-2c9d407204aa")
    public void testAppInstallationAndLaunch() throws Exception {
        Instrumentation instrumentation = testFramework.getInstrumentation();
        final UiDevice device = UiDevice.getInstance(instrumentation);
        final String application = "Google Voice";

        if (hasGooglePlay) {
            boolean playStoreInstalled = PlayStoreUtil.isPlayStoreInstalled(instrumentation);

            if (playStoreInstalled) {
                PlayStoreUtil.loginGooglePlay(instrumentation);
                selectApplication(instrumentation, application);
                new GoogleAppConfirmationWatcher(device).checkForCondition();

                assertTrue("Unable to install the application from Google Play",
                        PlayStoreUtil.installApplication(instrumentation));

                AppLauncher.launch(instrumentation, "Play Store");
                device.findObject(new UiSelector().text("OPEN")).clickAndWaitForNewWindow();
                assertTrue("App could not be opened",
                        new Wait().until(new Wait.ExpectedCondition() {
                            @Override
                            public boolean isTrue() {
                                return device.findObject(new UiSelector()
                                        .textContains(application)).exists();
                            }
                        }));

                AppLauncher.launch(instrumentation, "Play Store");
                assertTrue("Unable to uninstall the application from Google Play",
                        PlayStoreUtil.uninstallApplication(instrumentation));

                PlayStoreUtil.resetPlayStore(instrumentation);
                device.pressHome();
            }
        }
    }

    /**
     * Verify that Google Play can reach the payment method prompt during paid app installation
     * <p>
     * TT ID: bd9460a8-7b07-4cfc-901f-a99564533e51
     * <p>
     *   <pre>
     *   Test Steps:
     *   1. Start an emulator and launch home screen.
     *   2. Open Apps.
     *   3. Confirm that Play Store is present, then launch.
     *   4. Search for pay app in store.
     *   Verify:
     *      1. Confirm that user is presented with a Pay Button with a $.
     *   </pre>
     */

    @Test
    @TestInfo(id = "bd9460a8-7b07-4cfc-901f-a99564533e51")
    public void testPayAppVerification() throws Exception {
        Instrumentation instrumentation = testFramework.getInstrumentation();
        final UiDevice device = UiDevice.getInstance(instrumentation);
        final String application = "Pocket Casts";

        if (hasGooglePlay) {
            boolean playStoreInstalled = PlayStoreUtil.isPlayStoreInstalled(instrumentation);

            if (playStoreInstalled) {
                PlayStoreUtil.loginGooglePlay(instrumentation);
                selectApplication(instrumentation, application);
                new GoogleAppConfirmationWatcher(device).checkForCondition();

                assertTrue("Target application is not a pay app",
                        new Wait().until(new Wait.ExpectedCondition() {
                    @Override
                    public boolean isTrue() {
                        UiSelector payButton = new UiSelector()
                                .className("android.widget.Button").packageName(
                                        Res.GOOGLE_PLAY_VENDING_RES);
                        return device.findObject(payButton.textContains("$")).exists();
                    }
                }));

                PlayStoreUtil.resetPlayStore(instrumentation);
                device.pressHome();
            }
        }
    }

    /**
     * Verify that Google Play search can be limited through parental controls
     * <p>
     * TT ID: fe78dba5-a0f2-4acf-bcbb-10b1c15d3484
     * <p>
     *   <pre>
     *   Test Steps:
     *   1. Start an emulator and launch home screen.
     *   2. Open Apps.
     *   3. Confirm that Play Store is present, then launch.
     *   4. Search for adult app in Play Store, successfully.
     *   5. Open Play Store settings.
     *   6. Turn on Parental Controls.
     *   7. Select restrictions for Apps and Games.
     *   8. Set and confirm a content PIN.
     *   9. Set controls to Everyone 10+.
     *   10. Search for adult app and family app in Play Store, finding only family app.
     *   11. Turn off Parental Controls.
     *   Verify:
     *      1. Confirm that search returns adult version of app without parental controls set.
     *      2. Confirm that search does not return adult version of app with parental controls set,
     *          but does return family version of app.
     *   </pre>
     */

    @Test
    @TestInfo(id = "fe78dba5-a0f2-4acf-bcbb-10b1c15d3484")
    public void testParentalControls() throws Exception {
        final Instrumentation instrumentation = testFramework.getInstrumentation();
        final UiDevice device = UiDevice.getInstance(instrumentation);
        final String familyApplication = "YouTube Kids";
        final String restrictedApplication = "Tinder";

        if (testFramework.getApi() >= 24 && testFramework.isGoogleApiAndPlayImage()) {
            boolean playStoreInstalled = PlayStoreUtil.isPlayStoreInstalled(instrumentation);

            if (playStoreInstalled) {
                PlayStoreUtil.loginGooglePlay(instrumentation);
                assertTrue("Adult application is not found in search.",
                        hasTestApp(instrumentation, restrictedApplication));

                setRestrictions(instrumentation,  "Apps", "Everyone 10+");


                assertTrue("Adult application found in search.",
                        !hasTestApp(instrumentation, restrictedApplication) &&
                                hasTestApp(instrumentation, familyApplication));

                toggleParentalControls(device, false);
            }
            device.pressHome();
        }
    }

    /**
     * Selects an application listed in Play Store, if found.
     */
    private static void selectApplication(Instrumentation instrumentation,
                                          String application) throws Exception {
        final UiDevice device = UiDevice.getInstance(instrumentation);

        boolean isFound = hasTestApp(instrumentation, application);
        if (isFound) {
            device.findObject(new UiSelector()
                    .descriptionContains(application)).clickAndWaitForNewWindow();
        }
    }

    /**
     * Helper to search Google Play for an application by description.
     * Return true if found, false if not.
     */
    private static boolean hasTestApp(Instrumentation instrumentation, String application)
            throws Exception {
        final UiDevice device = UiDevice.getInstance(instrumentation);
        final String appTitle = application;

        device.pressHome();
        PlayStoreUtil.launchGooglePlay(instrumentation, appTitle);

        return new Wait().until(new Wait.ExpectedCondition() {
            @Override
            public boolean isTrue() {
                boolean hasApplication =
                        device.findObject(new UiSelector().text(appTitle).
                                resourceId(Res.GOOGLE_PLAY_LIST_TITLE_RES)).exists();
                return hasApplication;
            }
        });
    }
    /**
     * Opens the Parental Controls menu
     */
    private static void openParentalControls(UiDevice testDevice) throws Exception {
        final UiDevice device = testDevice;
        device.findObject(new UiSelector().description("Back")).clickAndWaitForNewWindow();
        device.findObject(new UiSelector().description("Show navigation drawer"))
                .waitForExists(TimeUnit.SECONDS.toMillis(3));
        device.findObject(new UiSelector().description("Show navigation drawer"))
                .clickAndWaitForNewWindow();

        final UiScrollable scrollable = new UiScrollable(new UiSelector().scrollable(true));
        final UiObject settingsLink = scrollable.getChild(new UiSelector().text("Settings"));
        settingsLink.waitForExists(3L);
        if (!settingsLink.exists()) {
            new Wait().until(new Wait.ExpectedCondition() {
                @Override
                public boolean isTrue() throws UiObjectNotFoundException {
                    int swipes = 0;
                    while (!settingsLink.exists() && swipes < 20) {
                        scrollable.flingForward();
                        swipes++;
                    }
                    return settingsLink.exists();
                }
            });
        }
        if (settingsLink.exists()) {
            settingsLink.clickAndWaitForNewWindow();
        }

        final UiObject parentalControlsButton = scrollable.getChild(new UiSelector().text(
                "Parental controls"));
        parentalControlsButton.waitForExists(3L);
        if (!parentalControlsButton.exists()) {
            new Wait().until(new Wait.ExpectedCondition() {
                @Override
                public boolean isTrue() throws UiObjectNotFoundException {
                    scrollable.scrollIntoView(parentalControlsButton);
                    return parentalControlsButton.exists();
                }
            });
        }
        if (parentalControlsButton.exists()) {
            parentalControlsButton.clickAndWaitForNewWindow();
        }
    }

    /**
     * Toggles the Parental Controls button; on if true, off if false
     */
    private static void toggleParentalControls(UiDevice testDevice, boolean setChecked) throws Exception {
        final UiDevice device = testDevice;
        openParentalControls(device);

        final UiObject toggleButton = device.findObject(new UiSelector().resourceId(
                Res.GOOGLE_PLAY_FILTER_TOGGLE_RES));

        boolean toggleButtonExists = new Wait().until(new Wait.ExpectedCondition() {
            @Override
            public boolean isTrue() {
                return toggleButton.exists();
            }
        });

        if (toggleButtonExists && toggleButton.isChecked() != setChecked) {
            toggleButton.clickAndWaitForNewWindow();
            setParentalControlPin(device, "1111");
        }
    }

    /**
     * Change parental control restrictions in an application category to the given ages
     */
    private static void setRestrictions(Instrumentation instrumentation,
                                        String category, String ages) throws Exception {
        final UiDevice device = UiDevice.getInstance(instrumentation);
        final String appCategory = category;
        toggleParentalControls(device, true);

        new Wait().until(new Wait.ExpectedCondition() {
            @Override
            public boolean isTrue() {
                return device.findObject(new UiSelector().textStartsWith(appCategory)).exists();
            }
        });
        device.findObject(new UiSelector().textStartsWith(appCategory)).clickAndWaitForNewWindow();
        setParentalControlPin(device, "1111");
        device.findObject(new UiSelector().text(ages))
                .waitForExists(TimeUnit.SECONDS.toMillis(3));
        device.findObject(new UiSelector().text(ages))
                .clickAndWaitForNewWindow();
        new PlayStoreControlsWatcher(device).checkForCondition();
        UiScrollable scrollable = new UiScrollable(new UiSelector().scrollable(true));
        scrollable.waitForExists(3L);
        if (scrollable.exists()) {
            scrollable.flingToEnd(5);
        }
        new PlayStoreControlsWatcher(device).checkForCondition();
        PlayStoreUtil.resetPlayStore(instrumentation);
        device.pressHome();
    }
    /**
     * Sets and then confirms a parental control pin
     */
    private static void setParentalControlPin(UiDevice testDevice, String pin) throws Exception {
        final UiDevice device = testDevice;

        boolean hasPinDialog = new Wait().until(new Wait.ExpectedCondition() {
            @Override
            public boolean isTrue() throws UiObjectNotFoundException {
                return device.findObject(new UiSelector().text("Type PIN")).exists();
            }
        });

        if (!hasPinDialog) {
            return;
        }

        device.findObject(new UiSelector().text("Type PIN")).setText(pin);
        device.findObject(new UiSelector().text("OK")).clickAndWaitForNewWindow();

        boolean needsConfirmation = new Wait().until(new Wait.ExpectedCondition() {
            @Override
            public boolean isTrue() throws UiObjectNotFoundException {
                return device.findObject(new UiSelector().text("Type PIN")).exists();
            }
        });

        if (needsConfirmation) {
            device.findObject(new UiSelector().text("Type PIN")).setText(pin);
            device.findObject(new UiSelector().text("OK")).clickAndWaitForNewWindow();
        }
    }
}