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
import com.android.devtools.systemimage.uitest.utils.NetworkUtil;
import com.android.devtools.systemimage.uitest.utils.SystemUtil;
import com.android.devtools.systemimage.uitest.utils.Wait;
import com.android.devtools.systemimage.uitest.watchers.NetworkUtilPopupWatcher;

import org.junit.Ignore;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.Timeout;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;

import android.app.Instrumentation;
import android.content.ContentResolver;
import android.content.Context;
import android.support.test.runner.AndroidJUnit4;
import android.support.test.uiautomator.By;
import android.support.test.uiautomator.UiDevice;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiObjectNotFoundException;
import android.support.test.uiautomator.UiScrollable;
import android.support.test.uiautomator.UiSelector;
import android.support.test.uiautomator.Until;
import android.provider.Settings;

import junit.framework.Assert;

import java.util.concurrent.TimeUnit;

/**
 * Test class for network connection on emulator.
 */
@RunWith(AndroidJUnit4.class)
public class NetworkIOTest {
    private final String TAG = "NetworkIOTest";

    @Rule
    public final SystemImageTestFramework testFramework = new SystemImageTestFramework();

    @Rule
    public Timeout globalTimeout = Timeout.seconds(240);

    private final int api = testFramework.getApi();

    /**
     * Verifies test browser successfully loads a web page.
     * <p>
     * This is run to qualify releases. Please involve the test team in substantial changes.
     * <p>
     * TR ID: C14578825
     * <p>
     *   <pre>
     *   Test Steps:
     *   1. Start the emulator.
     *   2. Launch browser app.
     *   3. Navigate to a website.
     *   Verify:
     *   Icons indicating working network connection displayed in status bar.
     *   Browser successfully loads the web page.
     *   </pre>
     */
    @Test
    @TestInfo(id = "14578825")
    public void testBrowserLoadsSite() throws Exception {
        Instrumentation instrumentation = testFramework.getInstrumentation();
        UiDevice device = testFramework.getDevice();

        // Check network connectivity.
        if (NetworkUtil.hasCellularNetworkConnection(instrumentation)) {
            if (api < 24) {
                AppLauncher.launch(instrumentation, "Browser");
                device.findObject(new UiSelector().resourceId(
                        Res.BROWSER_URL_TEXT_FIELD_RES)).click();
                device.findObject(new UiSelector().resourceId(Res.BROWSER_URL_TEXT_FIELD_RES))
                        .clearTextField();
                device.findObject(new UiSelector().resourceId(Res.BROWSER_URL_TEXT_FIELD_RES))
                        .setText("google.com");
                device.pressEnter();

                // Verify if the load bar is there at first,
                // then verify if the loading bar finishes in 3 seconds (default timeout on Wait()).
                final UiObject progress =
                        device.findObject(new UiSelector().resourceId(Res.BROWSER_SEARCH_ICON_RES));
                boolean isSuccess =
                        new Wait().until(new Wait.ExpectedCondition() {
                            @Override
                            public boolean isTrue() throws Exception {
                                return !progress.exists();
                            }
                        });
                assertTrue("Failed to dismiss the loading bar.", isSuccess);
            }  else if (testFramework.isGoogleApiImage() || testFramework.isGoogleApiAndPlayImage()) {
                device.openNotification();
                String cellularData = api >= 26 ? "Mobile data" : "Mobile Cellular Data";
                boolean hasCellularData =
                        device.wait(
                                Until.hasObject(By.descContains(cellularData)),
                                TimeUnit.MILLISECONDS.convert(3L, TimeUnit.SECONDS)
                        );
                assertTrue("Could not connect to the network.", hasCellularData);
                device.pressHome();

                AppLauncher.launch(instrumentation, "Chrome");
                // If this is the first launch, dismiss the "Welcome to Chrome" screen.
                UiObject acceptButton = device.findObject(new UiSelector().resourceId(
                        Res.CHROME_TERMS_ACCEPT_BUTTON_RES));
                if (acceptButton.exists()) {
                    acceptButton.clickAndWaitForNewWindow();
                }

                // Dismiss the "Sign in to Chrome" screen if it's there.
                UiObject noThanksButton = device.findObject(new UiSelector().resourceIdMatches(
                        Res.CHROME_NO_THANKS_BUTTON_RES));
                if (noThanksButton.waitForExists(TimeUnit.SECONDS.toMillis(3))) {
                    noThanksButton.clickAndWaitForNewWindow();
                }

                UiObject searchBox = device.findObject(new UiSelector().resourceId(
                        Res.CHROME_SEARCH_BOX_RES));
                if (searchBox.exists()) {
                    searchBox.clickAndWaitForNewWindow();
                }

                final UiObject textField = device.findObject(new UiSelector().resourceId(
                        Res.CHROME_URL_BAR_RES));
                Assert.assertTrue("Chrome URL bar not found",
                        new Wait().until(new Wait.ExpectedCondition() {
                            @Override
                            public boolean isTrue() throws Exception {
                                return textField.exists();
                            }
                        }));

                textField.click();
                textField.clearTextField();
                textField.setText("google.com");
                device.pressEnter();

                // Verify if the load bar is there at first. Then verify if the loading bar
                // finishes within the default timeout on Wait().
                final UiObject progress =
                        device.findObject(new UiSelector().resourceId(Res.CHROME_PROGRESS_BAR_RES));
                boolean isSuccess =
                        new Wait().until(new Wait.ExpectedCondition() {
                            @Override
                            public boolean isTrue() throws Exception {
                                return !progress.exists();
                            }
                        });
                assertTrue("Failed to dismiss the loading bar.", isSuccess);

            }
        }
    }

    /**
     * Verifies cellular data can be enabled and disabled.
     * <p>
     * This is run to qualify releases. Please involve the test team in substantial changes.
     * <p>
     * TR ID: C14581152
     * <p>
     *   <pre>
     *   Test Steps:
     *   1. Start the emulator.
     *   2. Open Settings > Wireless and Networks > Data Usage
     *   3. Check if billing cycle is enabled, toggle Cellular data switch on if not.
     *   4. Toggle Cellular data switch off.
     *   5. Toggle Cellular data switch on.
     *   Verify:
     *   1. Cellular data is turned off.
     *   1. Cellular data is turned on.
     *   </pre>
     * <p>
     * The test works on API 23 and greater.
     */
    @Test
    @TestInfo(id = "14581152")
    public void toggleCellularDataMode() throws Exception {
        final Instrumentation instrumentation = testFramework.getInstrumentation();
        UiDevice device = UiDevice.getInstance(instrumentation);
        String[] path = api >= 26 ? new String[] {"Settings", "Network & Internet", "Data usage"} :
                new String[] {"Settings", "Data usage"};
        String label = api >= 26 ? "Mobile data" : "Cellular data";
        final UiObject dataSwitch = device.findObject(new UiSelector().text(label));

        UiScrollable scrollable = new UiScrollable(new UiSelector().scrollable(true));
        final UiObject billingCycle = api >= 24 ? device.findObject(new UiSelector().text("Billing cycle")) :
                device.findObject(new UiSelector().text("Set cellular data limit"));

        if (api >= 23) {
            AppLauncher.launchPath(instrumentation, path);

            if (scrollable.waitForExists(3L)) {
                scrollable.scrollIntoView(billingCycle);
            }
            assertTrue("Data switch not found.", new Wait().until(new Wait.ExpectedCondition() {
                @Override
                public boolean isTrue() {
                    return dataSwitch.exists();
                }
            }));

            if (!billingCycle.exists() || !billingCycle.isEnabled()) {
                dataSwitch.click();
                new NetworkUtilPopupWatcher(device).checkForCondition();
            }

            // Disable Cellular data.
            dataSwitch.click();
            TimeUnit.SECONDS.sleep(3); //  Require a sleep to avoid flakiness on buildbot.
            new NetworkUtilPopupWatcher(device).checkForCondition();

            assertTrue("Disabled billing cycle label not found.", new Wait().until(new Wait.ExpectedCondition() {
                @Override
                public boolean isTrue() throws UiObjectNotFoundException {
                    return !billingCycle.exists() || !billingCycle.isEnabled();
                }
            }));

            // Enable Cellular data.
            dataSwitch.click();
            TimeUnit.SECONDS.sleep(3); //  Require a sleep to avoid flakiness on buildbot.
            new NetworkUtilPopupWatcher(device).checkForCondition();

            assertTrue("Enabled billing cycle label not found.", new Wait().until(new Wait.ExpectedCondition() {
                @Override
                public boolean isTrue() throws UiObjectNotFoundException {
                    return billingCycle.exists() && billingCycle.isEnabled();
                }
            }));
        }
    }

    /**
     * Verifies enabling airplane mode
     *   <pre>
     *   Test Steps:
     *   1. Start the emulator.
     *   2. Open Settings
     *   3. Locate Airplane mode toggle switch.
     *   4. Toggle Airplane mode on.
     *   Verify:
     *   Airplane mode icon is present and enabled in notification tray
     *   5. Toggle Airplane mode off.
     *   </pre>
     * <p>
     * The test works on API 23 and greater.
     */
    @Test
    @TestInfo(id = "14581152")
    public void enableAirplaneMode() throws Exception {
        final Instrumentation instrumentation = testFramework.getInstrumentation();
        UiDevice device = UiDevice.getInstance(instrumentation);

        if (api >= 23) {
            String[] path = api >= 26 ? new String[]{"Settings", "Network & Internet"} :
                    new String[]{"Settings", "More"};
            AppLauncher.launchPath(instrumentation, path);

            // Test requires "Airplane mode" switch widget to start in the off state.
            if (NetworkUtil.isAirplaneModeEnabled(device)) {
                AppLauncher.launchPath(instrumentation, path);
                toggleAirplaneMode(device);
            }
            assertFalse("Airplane mode is not disabled.", NetworkUtil.isAirplaneModeEnabled(device));

            AppLauncher.launchPath(instrumentation, path);
            toggleAirplaneMode(device);
            assertTrue("Airplane mode is not enabled.", NetworkUtil.isAirplaneModeEnabled(device));

            // Disable airplane mode.
            AppLauncher.launchPath(instrumentation, path);
            toggleAirplaneMode(device);
        }
    }

    /**
     * Verifies repeatedly enabling and disabling airplane mode
     *   <pre>
     *   Test Steps:
     *   1. Start the emulator.
     *   2. Open Settings
     *   3. Locate Airplane mode toggle switch.
     *   4. Toggle Airplane mode on.
     *   Verify:
     *   Airplane mode icon is present and enabled in notification tray
     *   5. Toggle Airplane mode off.
     *   6  Repeat steps 3-6 four more times.
     *   </pre>
     * <p>
     * The test works on API 23 and greater.
     */
    @Ignore
    @TestInfo(id = "14581152")
    public void stressTestAirplaneMode() throws Exception {
        final Instrumentation instrumentation = testFramework.getInstrumentation();
        UiDevice device = UiDevice.getInstance(instrumentation);
        int stressCount = 5;

        if (api >= 23) {
            String[] path = api >= 26 ? new String[]{"Settings", "Network & Internet"} :
                    new String[]{"Settings", "More"};
            AppLauncher.launchPath(instrumentation, path);

            // Test requires "Airplane mode" switch widget to start in the off state.
            if (NetworkUtil.isAirplaneModeEnabled(device)) {
                AppLauncher.launchPath(instrumentation, path);
                toggleAirplaneMode(device);
            }
            assertFalse("Airplane mode is not disabled.", NetworkUtil.isAirplaneModeEnabled(device));

            for (int i = 0; i < stressCount; i++) {
                AppLauncher.launchPath(instrumentation, path);
                toggleAirplaneMode(device);
                assertTrue("Airplane mode is not enabled.", NetworkUtil.isAirplaneModeEnabled(device));
                new Wait(TimeUnit.MILLISECONDS.convert(3L, TimeUnit.SECONDS));

                // Disable airplane mode.
                AppLauncher.launchPath(instrumentation, path);
                toggleAirplaneMode(device);
                assertFalse("Airplane mode is not disabled.", NetworkUtil.isAirplaneModeEnabled(device));
                new Wait(TimeUnit.MILLISECONDS.convert(3L, TimeUnit.SECONDS));
            }
        }
    }

    /**
     * Verifies disabling 3G Data mode
     *   <pre>
     *   Test Steps:
     *   1. Start the emulator.
     *   2. Open Settings
     *   3. Launch Preferred Network Type
     *   4. Enable 3G Data mode if not enabled.
     *   5. Toggle 2G Data mode on.
     *   Verify:
     *   2G Data mode icon is set as the Preferred Network Type
     *   6. Toggle 3G Data mode on to reset image.
     *   </pre>
     * <p>
     * The test works on API 19 and greater.
     */
    @Test
    @TestInfo(id = "14581152")
    public void disable3GData() throws Exception {
        final Instrumentation instrumentation = testFramework.getInstrumentation();
        UiDevice device = UiDevice.getInstance(instrumentation);

        if (api >= 19) {
            String[] path;
            if (api >= 27) {
                path = new String[]{"Settings", "Network & Internet", "Mobile network", "Advanced", "Preferred network type"};
            } else if (api == 26) {
                path = new String[]{"Settings", "Network & Internet", "Mobile network", "Preferred network type"};
            } else if (api >= 21){
                path = new String[]{"Settings", "More", "Cellular networks", "Preferred network type"};
            } else {
                path = new String[]{"Settings", "More", "Mobile networks", "Preferred network type"};
            }

            AppLauncher.launchPath(instrumentation, path);

            UiObject dataSwitch3G = device.findObject(new UiSelector().text("3G"));
            UiObject dataSwitch2G = device.findObject(new UiSelector().text("2G"));

            // Test requires image to start in 3G data mode.
            if (!dataSwitch3G.isChecked()) {
                dataSwitch3G.clickAndWaitForNewWindow();
                UiObject preferredNetwork = device.findObject(new UiSelector().text("Preferred network type"));
                if (preferredNetwork.exists()) {
                    preferredNetwork.clickAndWaitForNewWindow();
                }
            }
            // Enable 2G data mode option.
            dataSwitch2G.click();

            final UiObject data2GPreferred = device.findObject(new UiSelector().text("2G").
                    packageName(Res.ANDROID_PHONE_RES));

            // Wait for 2G data mode icon
            boolean data2GModeActive = new Wait().until(new Wait.ExpectedCondition() {
                @Override
                public boolean isTrue() throws Exception {
                    return data2GPreferred.exists();
                }
            });

            assertTrue("3G data mode is not disabled.", data2GModeActive);

            // Reset 3G mode.
            data2GPreferred.clickAndWaitForNewWindow();
            dataSwitch3G.click();
        }
    }

    /**
     * Verifies disabling data roaming mode
     *   <pre>
     *   Test Steps:
     *   1. Start the emulator.
     *   2. Open Settings
     *   3. Launch Mobile network
     *   4. Enable data Roaming if not enabled.
     *   5. Toggle data Roaming mode off.
     *   Verify:
     *   Data Roaming is not set in the Telephony manager
     *   6. Toggle data roaming on to reset image.
     *   </pre>
     * <p>
     * The test works on API 18-25.
     * Note: This test cannot be run on API's 26 and greater due to a security exception thrown
     * by Settings.Global in checkRoamingStatus();
     */
    @Test
    @TestInfo(id = "14581152")
    public void disableDataRoaming() throws Exception {
        final Instrumentation instrumentation = testFramework.getInstrumentation();
        UiDevice device = UiDevice.getInstance(instrumentation);
        Context context = testFramework.getInstrumentation().getContext();

        if (api >= 18 && api <= 25) {
            String[] path;
            if (api >= 21) {
                path = new String[]{"Settings", "More", "Cellular networks"};
            } else {
                path = new String[]{"Settings", "More", "Mobile networks"};
            }

            AppLauncher.launchPath(instrumentation, path);

            // Test requires image to start with data roaming active.
            if (!isDataRoamingEnabled(context)) {
                toggleRoaming(device);
            }

            assertTrue("Data roaming is not enabled.", isDataRoamingEnabled(context));

            // Disable data roaming option.
            toggleRoaming(device);

            assertFalse("Data roaming is not disabled.", isDataRoamingEnabled(context));

            toggleRoaming(device);

        }
    }

    /**
     * Helper class to toggle the active data roaming status
     */
    private void toggleAirplaneMode(UiDevice device) throws UiObjectNotFoundException {
        UiObject airplaneModeText = device.findObject(
                new UiSelector().text("Airplane mode"));
        boolean isFound = airplaneModeText.waitForExists(3L);
        if (isFound) {
            airplaneModeText.clickAndWaitForNewWindow();
        }
    }


    /**
     * Helper class to determine if data roaming is enabled
     * Note: this method is blocked on API's 26 and higher by a java.lang.SecurityException
     */
    private boolean isDataRoamingEnabled(Context context) throws Exception {
        try {
            String key = Settings.Global.DATA_ROAMING;
            ContentResolver cr = context.getContentResolver();
            return Settings.Global.getInt(cr, key, 0) == 1 ? true : false;
        } catch (Exception exception) {
            return false;
        }
    }

    /**
     * Helper class to toggle the active data roaming status
     */
    private void toggleRoaming(UiDevice device) throws UiObjectNotFoundException {
        UiObject dataRoamingSwitch = device.findObject(new UiSelector().text("Data roaming"));
        dataRoamingSwitch.clickAndWaitForNewWindow();
        UiObject allowRoaming = device.findObject(new UiSelector().text("OK"));
        if (allowRoaming.exists()) {
            allowRoaming.clickAndWaitForNewWindow();
        }
    }
}