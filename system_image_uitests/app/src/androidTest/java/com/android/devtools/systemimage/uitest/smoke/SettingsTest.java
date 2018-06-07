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
import com.android.devtools.systemimage.uitest.utils.AppManager;
import com.android.devtools.systemimage.uitest.utils.DeveloperOptionsManager;
import com.android.devtools.systemimage.uitest.utils.ApiDemosInstaller;
import com.android.devtools.systemimage.uitest.utils.PackageInstallationUtil;
import com.android.devtools.systemimage.uitest.utils.SettingsUtil;
import com.android.devtools.systemimage.uitest.utils.UiAutomatorPlus;
import com.android.devtools.systemimage.uitest.utils.Wait;
import com.android.devtools.systemimage.uitest.watchers.SettingsTestPopupWatcher;
import com.android.devtools.systemimage.uitest.watchers.CameraAccessPermissionsWatcher;

import org.junit.Assert;
import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.Timeout;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;

import android.app.Instrumentation;
import android.support.test.runner.AndroidJUnit4;
import android.support.test.uiautomator.By;
import android.support.test.uiautomator.UiDevice;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiObject2;
import android.support.test.uiautomator.UiObjectNotFoundException;
import android.support.test.uiautomator.UiScrollable;
import android.support.test.uiautomator.UiSelector;
import android.util.Log;
import android.widget.LinearLayout;
import android.widget.Switch;
import android.widget.TextView;

/**
 * Test class for Android Settings page on Google API images.
 */
@RunWith(AndroidJUnit4.class)
public class SettingsTest {
    @Rule
    public final SystemImageTestFramework testFramework = new SystemImageTestFramework();

    private Instrumentation instrumentation = testFramework.getInstrumentation();
    private UiDevice device = UiDevice.getInstance(instrumentation);

    private int api = testFramework.getApi();
    private final static String TAG = "SettingsTest";

    // Tests under this class takes up to 240 seconds depending on the performance of the bot the
    // tests run on.
    @Rule
    public Timeout globalTimeout = Timeout.seconds(240);

    @Before
    public void activateDeviceAdmin() throws Exception {
        ApiDemosInstaller.installApp(instrumentation);
    }

    /**
     * Verifies Location page opens on Google API images.
     * <p>
     * This is run to qualify releases. Please involve the test team in substantial changes.
     * <p>
     * TT ID: 97d93bb7-63d2-4e89-9d18-0f232bbd51ab
     * <p>
     *   <pre>
     *   1. Start the emulator.
     *   2. Open Settings > Google > Location
     *   Verify:
     *   Location settings page opens.
     *   </pre>
     */
    @Test
    @TestInfo(id = "97d93bb7-63d2-4e89-9d18-0f232bbd51ab")
    public void testLocationSettingsPageOpen() throws Exception {
        if (!testFramework.isGoogleApiAndPlayImage() && !testFramework.isGoogleApiImage() ||
                api < 23) {
            return;
        }

        AppLauncher.launch(instrumentation, "Settings");
        UiScrollable itemList =
                new UiScrollable(
                        new UiSelector().resourceIdMatches(Res.SETTINGS_LIST_CONTAINER_RES)
                );
        itemList.setAsVerticalList();
        if(api >= 26) {
            String securityLabel = api == 26 ? "Security & Location" : "Security & location";
            UiObject security = itemList.getChildByText(new UiSelector().className("android.widget.TextView"),
                    securityLabel);
            security.clickAndWaitForNewWindow();
        }
        UiObject location =
                itemList.getChildByText(new UiSelector().className("android.widget.TextView"),
                        "Location");
        location.clickAndWaitForNewWindow();

        boolean isLocationDisabled = new Wait().until(new Wait.ExpectedCondition() {
            @Override
            public boolean isTrue() throws UiObjectNotFoundException {
                return device.findObject(new UiSelector().textMatches("(?i)yes")).exists();
            }
        });

        if (isLocationDisabled) {
            device.findObject(new UiSelector().textMatches("(?i)yes")).clickAndWaitForNewWindow();
            device.findObject(new UiSelector().textMatches("(?i)location")).clickAndWaitForNewWindow();
        }
        assertTrue("Failed to find Location title.",
                new Wait().until(new Wait.ExpectedCondition() {
                    @Override
                    public boolean isTrue() throws Exception {
                        return device.findObject(new UiSelector().text("Location")).exists() &&
                                device.findObject(new UiSelector().text("Recent location requests"))
                                        .exists();
                    }
                }));
    }

    /**
     * Verifies that the phone cannot dial out if phone privileges have been disabled.
     * <p>
     * This is run to qualify releases. Please involve the test team in substantial changes.
     * <p>
     * TT ID: 4f09278e-d1e3-47bb-a22c-70f236ac9a48
     * <p>
     *   <pre>
     *  1. Start the emulator.
     *  2. Open Settings > Apps
     *  3. Click on the gear icon and select App permissions.
     *  4. Click on "Phone"
     *  5. Disable Phone permissions.
     *  6. Click on DENY button.
     *  7. Return to the main screen.
     *  8. Launch the phone app.
     *  9. Click on the dialer icon.
     *  10. Type in a number.
     *  11. Click on Call icon.
     *   Verify:
     *   Dialog stating "This application cannot make outgoing calls without the Phone permission."
     *   </pre>
     * <p>The test works on API 23 and greater. No gear menu and app permissions for APIs under 23.
     *
     */
    @Test
    @TestInfo(id = "4f09278e-d1e3-47bb-a22c-70f236ac9a48")
    public void testPhonePermissions() throws Exception {
        final String app = "Phone";

        if (api < 23) {
            return;
        }

        SettingsUtil.setAppPermissions(instrumentation, app, app, false);
        device.pressHome();

        AppLauncher.launch(instrumentation, app);

        device.findObject(new UiSelector().resourceIdMatches(Res.DIALER_PHONE_RES)).
                clickAndWaitForNewWindow();
        device.findObject(new UiSelector().resourceIdMatches(Res.DIALER_DIGITS_RES)).setText("555");
        device.findObject(new UiSelector().resourceIdMatches(Res.DIALER_PAD_RES)).click();

        assertTrue("Did not prompt for lack of Phone permission.",
                new Wait().until(new Wait.ExpectedCondition() {
                    @Override
                    public boolean isTrue() throws Exception {
                        return device.findObject(new UiSelector().text(
                                "This application cannot make outgoing calls without the Phone permission.")).
                                        exists();
                        }
                })
        );

        SettingsUtil.setAppPermissions(instrumentation, app, app, true);
        device.pressHome();

    }

    /**
     * Verifies that access must be confirmed if Maps location permissions are disabled.
     * <p>
     * This is run to qualify releases. Please involve the test team in substantial changes.
     * <p>
     * TT ID: 4f09278e-d1e3-47bb-a22c-70f236ac9a48
     * <p>
     *   <pre>
     *  1. Start the Emulator.
     *  2. Open Settings > Apps
     *  3. Click on the gear icon and select App permissions.
     *  4. Click on Location from App permissions screen.
     *  5. Disable Maps.
     *  6. Launch Maps app.
     *  7. Click on the locator icon.
     *   Verify:
     *   Dialog asking "Allow Maps to access this device's location?"
     *   </pre>
     * <p>
     * The test works on API 23 and greater, with google APIs only.
     * No gear menu and app permissions for APIs under 23, and no maps without google APIs.
     */
    @Test
    @TestInfo(id = "4f09278e-d1e3-47bb-a22c-70f236ac9a48")
    public void testMapPermissions() throws Exception {
        final String appType = "Location";
        final String appName = "Maps";

        if (!testFramework.isGoogleApiAndPlayImage() && !testFramework.isGoogleApiImage() ||
                api < 23) {
            return;
        }

        SettingsUtil.setAppPermissions(instrumentation, appType, appName, false);
        device.pressHome();

        AppLauncher.launch(instrumentation, appName);
        final UiObject acceptAndContinueButton;
        acceptAndContinueButton = device.findObject(new UiSelector().
                textMatches("(?i)accept\\s&\\scontinue"));
        if (acceptAndContinueButton.exists())
            acceptAndContinueButton.clickAndWaitForNewWindow();
        final UiObject skipButton;
        skipButton = device.findObject(new UiSelector().textMatches("(?i)skip"));
        if (skipButton.exists())
            skipButton.clickAndWaitForNewWindow();
        final UiObject gotItButton;
        gotItButton = device.findObject(new UiSelector().textMatches("(?i)got\\sit"));
        if (gotItButton.exists())
            gotItButton.clickAndWaitForNewWindow();
        device.findObject(new UiSelector().description("Move to your location"))
                .clickAndWaitForNewWindow();
        assertTrue("Did not prompt for lack of Maps permission.",
                new Wait().until(new Wait.ExpectedCondition() {
                    @Override
                    public boolean isTrue() throws Exception {
                        return device.findObject(new UiSelector()
                                .text("Allow Maps to access this device's location?")).exists();
                    }
                })
        );

        SettingsUtil.setAppPermissions(instrumentation, appType, appName, true);
        device.pressHome();
    }

    /**
     * Verifies the App permissions screen loads.
     * <p>
     * This is run to qualify releases. Please involve the test team in substantial changes.
     * <p>
     * TT ID: 4f09278e-d1e3-47bb-a22c-70f236ac9a48
     * <p>
     *   <pre>
     *   1. Start the emulator.
     *   2. Open Settings > Apps
     *   3. Click on the gear icon.
     *   4. Click on App permissions.
     *   Verify:
     *   App permissions page loads. Able to identify various apps on the page.
     *   </pre>
     * <p>
     * The test works on API 23 and greater. No gear menu and app permissions for APIs under 23.
     */
    @Test
    @TestInfo(id = "4f09278e-d1e3-47bb-a22c-70f236ac9a48")
    public void displayConfigureAppPermissions() throws Exception {
        if (api < 23) {
            return;
        }
        if (api >= 26) {
            SettingsUtil.openItem(instrumentation, "Apps & notifications");
        } else {
            SettingsUtil.openItem(instrumentation, "Apps");
            device.findObject(new UiSelector().resourceId(Res.SETTINGS_ADVANCED_OPTION_RES))
                    .clickAndWaitForNewWindow();
        }

        device.findObject(new UiSelector().textContains("App permissions"))
                .clickAndWaitForNewWindow();

        assertTrue(device.findObject(new UiSelector().textContains("App permissions")).exists()
                && device.findObject(new UiSelector().textContains("Calendar")).exists()
                && device.findObject(new UiSelector().textContains("Camera")).exists()
                && device.findObject(new UiSelector().textContains("Contacts")).exists()
                && device.findObject(new UiSelector().textContains("Phone")).exists()
                && device.findObject(new UiSelector().description("Navigate up")).exists());
    }

    /**
     * Verifies Developer options is displayed under the System section on the Systems page.
     * <p>
     * This is run to qualify releases. Please involve the test team in substantial changes.
     * <p>
     * TT ID: 4578f63f-7d2e-4e5e-a4e0-0ce2ae67982e
     * <p>
     *   <pre>
     *   1. Start the emulator.
     *   2. Open Settings > About emulated device
     *   3. Click on the Build number option 7 times.
     *   4. Toast message indicating developer options is enabled. (Can't confirm due to b/26511336)
     *   5. Navigate to Settings page.
     *   Verify:
     *   Developer options displayed under Systems section on the Settings page.
     *   </pre>
     */
    @Test
    @TestInfo(id = "4578f63f-7d2e-4e5e-a4e0-0ce2ae67982e")
    public void developerOptionsEnabled() throws Exception {
        if (!DeveloperOptionsManager.isDeveloperOptionsEnabled(testFramework)) {
            DeveloperOptionsManager.enableDeveloperOptions(testFramework);
        } else {
            return;
        }
        assertTrue("Failed to enable Developer options.",
                DeveloperOptionsManager.isDeveloperOptionsEnabled(testFramework));
    }

    /**
     * Common code for finding a checkbox/switch in the Date & time settings.
     */
    private  UiObject2 navigateToDateTimeSwitch(String text) throws UiObjectNotFoundException {
        final String container = (api >= 24) ?
                Res.NETWORK_SWITCHES_RECYCLER_VIEW_RES :  Res.ANDROID_LIST_RES;
        final String label = "Date & time";

        try {
            if (api >= 26) {
                SettingsUtil.openItem(instrumentation, "System");
                device.findObject(new UiSelector().text(label))
                        .clickAndWaitForNewWindow();
            } else {
                SettingsUtil.openItem(instrumentation, label);
            }
        } catch (Exception e) {
            Log.e(TAG, e.getMessage());
        }

        UiObject2 dateTimeSwitch = null;

        try {
            final UiObject2 widget = UiAutomatorPlus.findObjectByRelative(
                    instrumentation,
                    By.clazz("android.widget.Switch"),
                    By.text(text),
                    By.res(container));
            dateTimeSwitch = widget;
        } catch (UiObjectNotFoundException e1) {
            try {
                final UiObject2 widget = UiAutomatorPlus.findObjectByRelative(
                        instrumentation,
                        By.clazz("android.widget.CheckBox"),
                        By.text(text),
                        By.res(container));
                dateTimeSwitch = widget;
            } catch (UiObjectNotFoundException e2)  {
                assertTrue("Could not find Date Time switch", false);
            }
        }
        return dateTimeSwitch;
    }

    /**
     * Verifies set date and set time fields are editable.
     * <p>
     * This is run to qualify releases. Please involve the test team in substantial changes.
     * <p>
     * TT ID: f83bf063-2a8c-4d1b-808b-20fd76933135
     * <p>
     *   <pre>
     *   1. Start the emulator.
     *   2. Open Settings > Date and time
     *   3. Automatic date & time option is enabled.
     *   4. Disable Automatic date & time option.
     *   5. Set date and Set time options are enabled.
     *   6. Click on Set date option and Set time option.
     *   Verify:
     *   Calendar frame and Clock frame appears respectively.
     *   </pre>
     */
    @Test
    @TestInfo(id = "f83bf063-2a8c-4d1b-808b-20fd76933135")
    public void enableSetDateAndSetTime() throws Exception {
        final UiObject2 widget = navigateToDateTimeSwitch("Automatic date & time");

        // Test requires "Automatic date & time" widget to start in the enabled state.
        if (!widget.isChecked()) {
            widget.click();
        }
        assertTrue("Failed to disable set date.",
              new Wait().until(new Wait.ExpectedCondition() {
                  @Override
                    public boolean isTrue() throws Exception {
                        return !device.findObject(new UiSelector().text("Set date")).isEnabled();
                  }
              })
        );
        assertTrue("Failed to disable set time.",
              new Wait().until(new Wait.ExpectedCondition() {
                  @Override
                    public boolean isTrue() throws Exception {
                        return !device.findObject(new UiSelector().text("Set time")).isEnabled();
                  }
              })
        );
        widget.click();
        assertTrue("Failed to enable set date.",
              new Wait().until(new Wait.ExpectedCondition() {
                  @Override
                    public boolean isTrue() throws Exception {
                        return device.findObject(new UiSelector().text("Set date")).isEnabled();
                  }
              })
        );
        assertTrue("Failed to enable set time.",
              new Wait().until(new Wait.ExpectedCondition() {
                  @Override
                    public boolean isTrue() throws Exception {
                        return device.findObject(new UiSelector().text("Set time")).isEnabled();
                  }
              })
        );
        device.findObject(new UiSelector().text("Set date")).clickAndWaitForNewWindow();
        if (api < 20) {
            assertTrue(device.findObject(
                    new UiSelector().resourceId(Res.ANDROID_DATE_PICKER_HEADER_RES_19)).exists());
            device.findObject(new UiSelector().textContains("Done")).click();
            device.findObject(new UiSelector().text("Set time")).click();
            assertTrue(device.findObject(
                    new UiSelector().resourceId(Res.ANDROID_TIME_HEADER_RES_19)).exists());

            device.findObject(new UiSelector().textContains("Done")).click();
        } else {
            assertTrue(device.findObject(
                    new UiSelector().resourceId(Res.ANDROID_DATE_PICKER_HEADER_RES)).exists());
            device.findObject(new UiSelector().textContains("CANCEL")).click();
            device.findObject(new UiSelector().text("Set time")).click();
            assertTrue(device.findObject(
                    new UiSelector().resourceId(Res.ANDROID_TIME_HEADER_RES)).exists());

            device.findObject(new UiSelector().textContains("CANCEL")).click();
        }
    }

    /**
     * Verifies Time Zone option can be enabled.
     * <p>
     * This is run to qualify releases. Please involve the test team in substantial changes.
     * <p>
     * TT ID: f83bf063-2a8c-4d1b-808b-20fd76933135
     * <p>
     *   <pre>
     *   1. Start the emulator.
     *   2. Open Settings > Date & Time
     *   3. Verify automatic time zone option is enabled.
     *   4. Disable automatic time zone.
     *   5. Verify Select time zone is enabled.
     *   6. Enable time zone.
     *   Verify:
     *   Select time zone text and timezone offset text can be seen.
     *   </pre>
     */
    @Test
    @TestInfo(id = "f83bf063-2a8c-4d1b-808b-20fd76933135")
    public void enableTimeZone() throws Exception {
        final UiObject2 widget = navigateToDateTimeSwitch("Automatic time zone");

        // Initialize automatic time zone option to enabled state.
        if (!widget.isChecked()) {
            widget.click();
        }
        assertTrue("Failed to disable select time zone",
              new Wait().until(new Wait.ExpectedCondition() {
                  @Override
                    public boolean isTrue() throws Exception {
                        return !device.findObject(new UiSelector().text("Select time zone")).isEnabled();
                  }
              })
        );
        // Disable automatic time zone option.
        widget.click();
        final UiObject selectTimeZone = device.findObject(
                new UiSelector().text("Select time zone"));
        assertTrue("Failed to enable select time zone",
              new Wait().until(new Wait.ExpectedCondition() {
                  @Override
                    public boolean isTrue() throws Exception {
                        return selectTimeZone.isEnabled();
                  }
              })
        );
        selectTimeZone.clickAndWaitForNewWindow();

        assertTrue("Failed to load Select time zone screen.",
              new Wait().until(new Wait.ExpectedCondition() {
                  @Override
                    public boolean isTrue() throws Exception {
                        return device.findObject(
                                new UiSelector().text("Select time zone")).exists();
                    }
              })
        );
        UiScrollable timeZoneList =
                new UiScrollable(new UiSelector().className("android.widget.ListView"));

        String timezoneOffset;
        if (api <= 19)
            timezoneOffset = "GMT-8:00";
        else
            timezoneOffset = "GMT-08:00";
        assertTrue(timeZoneList.getChildByText(
                new UiSelector().className("android.widget.TextView"), timezoneOffset).exists());
    }

    /**
     * Verifies 24-hour format is enabled.
     * <p>
     * This is run to qualify releases. Please involve the test team in substantial changes.
     * <p>
     * TT ID: f83bf063-2a8c-4d1b-808b-20fd76933135
     * <p>
     *   <pre>
     *   1. Start the emulator.
     *   2. Open Settings > Date & Time
     *   3. Verify 24-hour format option is disabled.
     *   4. Verify example time on screen shows 1:00 PM.
     *   5. Enable 24-hour format.
     *   Verify:
     *   Example time on screen shows 13:00.
     *   </pre>
     */
    @Test
    @TestInfo(id = "f83bf063-2a8c-4d1b-808b-20fd76933135")
    public void enableTwentyFourHourFormat() throws Exception {
        final UiObject2 widget = navigateToDateTimeSwitch("Use 24-hour format");

        // Initialize 24-hour format option to disabled state.
        if (widget.isChecked()) {
            widget.click();
        }
        assertTrue("Failed to find Use 24-hour format.",
              new Wait().until(new Wait.ExpectedCondition() {
                  @Override
                    public boolean isTrue() throws Exception {
                        return device.findObject(
                                new UiSelector().text("Use 24-hour format")).exists();
                  }
              })
        );
        assertTrue("Failed to find 1:00 PM.",
              new Wait().until(new Wait.ExpectedCondition() {
                  @Override
                    public boolean isTrue() throws Exception {
                        return device.findObject(new UiSelector().text("1:00 PM")).exists();
                  }
              })
        );
        // Enable 24-hour format.
        widget.click();
        assertTrue("Failed to find 13:00.",
              new Wait().until(new Wait.ExpectedCondition() {
                  @Override
                    public boolean isTrue() throws Exception {
                        return device.findObject(new UiSelector().text("13:00")).exists();
                  }
              })
        );
        // Clean up by disabling 24-hour format option.
        widget.click();
    }

    /**
     * Verify that activating and deactivating Device Administrators setting works.
     * <p>
     * This is run to qualify releases. Please involve the test team in substantial changes.
     * <p>
     * TR ID: C144630613
     * <p>
     *   <pre>
     *   Test Steps:
     *   1. Start an emulator AVD.
     *   2. Goto Settings —> Security —> Device Administration.
     *   3. Select Sample Device Admin.
     *   4. Goto to setting and deactivate policy.
     *   Verify:
     *   1. (Verify #1) that the "Sample Device Admin" policy is deactivated.
     *   2. (Verify #2) that the "Sample Device Admin" policy is activated.
     *   3. (Verify #3) that the "Sample Device Admin" policy is deactivated.
     *   </pre>
     */
    @Test
    @TestInfo(id = "T144630613")
    public void activateDeactivatePolicy() throws Exception {
        boolean isAPIDemoInstalled = PackageInstallationUtil.isPackageInstalled(instrumentation,
                "com.example.android.apis");

        if (isAPIDemoInstalled) {
            if (checkStatusOfPolicy()) {
                SettingsUtil.deactivate(instrumentation, "Sample Device Admin");
            }
            assertFalse(checkStatusOfPolicy());

            // Activate "Sample Device Admin" policy
            SettingsUtil.activate(instrumentation, "Sample Device Admin");
            assertTrue(checkStatusOfPolicy());

            // Deactivate "Sample Device Admin" policy
            SettingsUtil.deactivate(instrumentation, "Sample Device Admin");
            assertFalse(checkStatusOfPolicy());
        } else {
            Log.w(TAG,"activateDeactivatePolicy: required APK is missing");
        }
    }

    /**
     * Check if the the selected policy is checked or not.
     */
    private boolean checkStatusOfPolicy()
            throws Exception {
        UiSelector listViewSelector = new UiSelector().resourceId(Res.ANDROID_LIST_RES);

        new SettingsTestPopupWatcher(device).checkForCondition();
        assertTrue(device.findObject(listViewSelector).exists());

        // Get all the available "Device administrators" options
        int size = device.findObject(listViewSelector).getChildCount();

        // Verify that the correct checkbox (Sample Device Admin) is checked
        for (int i = 0; i < size; i++) {
            UiSelector sampleDeviceSelection = listViewSelector.childSelector(new
                    UiSelector().index(i));

            UiObject2 sampleDeviceAdminCheckbox = UiAutomatorPlus.findObjectByRelative(
                    instrumentation,
                    By.clazz("android.widget.CheckBox"),
                    By.text("Sample Device Admin"),
                    By.res(Res.ANDROID_LIST_RES));

            if (sampleDeviceAdminCheckbox != null) {
                boolean isChecked = sampleDeviceAdminCheckbox.isChecked();
                return isChecked;
            }
        }
        return false;
    }

    private UiObject findObjectInScrollable(UiSelector selector) throws UiObjectNotFoundException {
        UiScrollable scrollable = new UiScrollable(new UiSelector().scrollable(true));
        scrollable.scrollIntoView(selector);
        return scrollable.getChild(selector);
    }

    public void enableSampleDeviceAdmin() throws Exception {
        boolean isAPIDemoInstalled = PackageInstallationUtil.isPackageInstalled(instrumentation,
                "com.example.android.apis");

        if (isAPIDemoInstalled) {
            AppLauncher.launch(instrumentation, "Settings");
            findObjectInScrollable(new UiSelector().textContains("Security")).click();
            if (api >= 24) {
                findObjectInScrollable(new UiSelector().textContains("Device admin").
                        resourceId(Res.ANDROID_TITLE_RES)).click();
            } else {
                findObjectInScrollable(new UiSelector().text("Device administrators")).click();
            }

            device.findObject(new UiSelector().text("Sample Device Admin")).click();

            try {
                if (api >= 24) {
                    findObjectInScrollable(new UiSelector().textContains("Activate")).click();
                } else {
                    device.findObject(new UiSelector().textMatches("(?i)activate(?-i)")).click();
                }
            } catch (UiObjectNotFoundException e) {
                assertTrue("Could not find device administration buttons.",
                      new Wait().until(new Wait.ExpectedCondition() {
                          @Override
                            public boolean isTrue() throws Exception {
                                return device.findObject(new UiSelector().text("Cancel")).exists();
                          }
                      })
                );
                device.findObject(new UiSelector().text("Cancel")).click();
            }
            device.pressHome();
        } else {
            Log.w(TAG, "enableSampleDeviceAdmin: required APK is missing");
        }
    }

    private void setCameraEnabled(final boolean enableCameraDevices) throws Exception {
        boolean isAPIDemoInstalled = PackageInstallationUtil.isPackageInstalled(instrumentation,
                "com.example.android.apis");

        if (isAPIDemoInstalled) {
            final boolean enableCameras = enableCameraDevices;
            String cameraCheckboxLabel = enableCameras ? "Device cameras disabled" :
                    "Device cameras enabled";
            final UiObject enableCamerasCheckbox = device.findObject(
                    new UiSelector().text(cameraCheckboxLabel));

            AppLauncher.launch(instrumentation, "API Demos");
            boolean widgetExists = new Wait().until(new Wait.ExpectedCondition() {
                @Override
                public boolean isTrue() throws Exception {
                    return device.findObject(new UiSelector().textContains("App")).exists();
                }
            });
            if (widgetExists) {
                device.findObject(new UiSelector().textContains("App")).click();
            }
            widgetExists = new Wait().until(new Wait.ExpectedCondition() {
                @Override
                public boolean isTrue() throws Exception {
                    return device.findObject(new UiSelector().text("Device Admin")).exists();
                }
            });

            if (widgetExists) {
                device.findObject(new UiSelector().text("Device Admin")).click();
            }
            widgetExists = new Wait().until(new Wait.ExpectedCondition() {
                @Override
                public boolean isTrue() throws Exception {
                    return device.findObject(new UiSelector().text("General")).exists();
                }
            });
            if (widgetExists) {
                device.findObject(new UiSelector().text("General")).click();
            }

            widgetExists = new Wait().until(new Wait.ExpectedCondition() {
                @Override
                public boolean isTrue() throws Exception {
                    return enableCamerasCheckbox.exists();
                }
            });

            if (widgetExists) {
                enableCamerasCheckbox.click();
            }

            device.pressHome();
        } else {
            Log.w(TAG, "setCameraEnabled: required APK is missing");
        }
    }

    private void gotoCameraApp() throws Exception {
        AppLauncher.launch(instrumentation, "Camera");
        new CameraAccessPermissionsWatcher(device).checkForCondition();
    }

    private boolean verifyCameraAppDisabled() {
        return device.hasObject(By.textContains(
                "Camera has been disabled because of security policies")) ||
                device.hasObject(By.text("Can't connect to the camera."));
    }

    /**
     * Verify test Camera App is disabled in emulator when disabled in Device Admin.
     * <p>
     * This is run to qualify releases. Please involve the test team in substantial changes.
     * <p>
     * TT ID: 4db4a825-b584-4c68-a04d-c6a933b14e24
     * <p>
     *   <pre>
     *   Test Steps:
     *   1. Start an emulator AVD.
     *   2. Goto Settings —> Security —> Device Administration
     *   3. Select Sample Device Admin.
     *   4. Goto app API Demos —> App —> Device Admin —> General
     *   5. Select Enable All Device Cameras.
     *   6. Repeat steps 2-4.
     *   7. Select Disable All Device Cameras.
     *   8. Goto Home screen —> Click on Camera Application
     *   9. Repeat steps 2-4.
     *   10. Select Enable All Device Cameras.
     *   Verify:
     *   1. (Verify #1) camera app is enabled
     *   2. (Verify #2) camera app is disabled
     *   2. (Verify #2) camera app is enabled
     *   </pre>
     */
    @Test
    @TestInfo(id = "4db4a825-b584-4c68-a04d-c6a933b14e24")
    public void testCameraAppDisabled() throws Exception {
        enableSampleDeviceAdmin();
        if (verifyCameraAppDisabled()) {
            setCameraEnabled(true);
        }
        Assert.assertFalse(verifyCameraAppDisabled());

        setCameraEnabled(false);
        gotoCameraApp();
        new CameraAccessPermissionsWatcher(device).checkForCondition();
        Assert.assertTrue(verifyCameraAppDisabled());
        setCameraEnabled(true);
        Assert.assertFalse(verifyCameraAppDisabled());
    }

    /**
     * To verify that "Reset app preferences" restores permission restrictions.
     * <p>
     * This is run to qualify releases. Please involve the test team in substantial changes.
     * <p>
     * TT ID: d49facce-9be7-47e0-afde-2052d3c57a25
     * <p>
     *   <pre>
     *   Test Steps:
     *   1. Launch an emulator avd with wipe data.
     *   2. Open Settings > Apps.
     *   3. Open the menu (3 vertical dots) and tap on "Show System".
     *   4. Tap on any app, say Maps and select "Permissions".
     *   5. Enable all available permissions for the app.
     *   6. Press back button.
     *   7. Open the menu > Reset app preferences > Reset apps.
     *   Verify:
     *   1. App settings for Maps are reset to default (Verify that Permissions and notification
     *   settings for Maps are cleared).
     *   </pre>
     */
    @Test
    @TestInfo(id = "d49facce-9be7-47e0-afde-2052d3c57a25")
    public void modifyAndResetAppPermissions() throws Exception {
        String appName = "Maps";
        String contactsText = "Contacts";
        String locationText = "Location";
        String phoneText = "Phone";
        String storageText = "Storage";

        // Variables to store the state of permissions.
        boolean contactsSwitchState;
        boolean locationSwitchState;
        boolean phoneSwitchState;
        boolean storageSwitchState;

        //Check for Deny alert dialog button for location permissions.
        UiObject denyButton;

        if (api < 23) {
            return;
        }

        //Open System apps list.
        AppManager.openSystemAppList(instrumentation);

        // Find and click "Maps" in apps list.
        UiScrollable itemList =
                new UiScrollable(
                        new UiSelector().resourceIdMatches(Res.SETTINGS_LIST_CONTAINER_RES)
                );
        itemList.setAsVerticalList();

        itemList.scrollIntoView(new UiSelector().text(appName));
        itemList.getChildByText(new UiSelector().className(TextView.class.getName()), appName)
                .clickAndWaitForNewWindow();

        //Get application info list.
        UiScrollable appInfoList =
                new UiScrollable(
                        new UiSelector().resourceIdMatches(Res.SETTINGS_LIST_CONTAINER_RES)
                );

        //Choose permissions to edit them.
        appInfoList.getChildByText(new UiSelector().
                className(TextView.class.getName()),"Permissions").clickAndWaitForNewWindow();

        UiScrollable permissionList;
        if (api > 23) {
            permissionList = new UiScrollable(new UiSelector().
                    resourceIdMatches(Res.ANDROID_LIST_RES));
        } else {
            permissionList = new UiScrollable(new UiSelector().
                    resourceIdMatches("com.android.packageinstaller:id/list"));
        }

        //Get switch widgets UiObjects.
        UiObject contactSwitch =
                findObjectByRelative(permissionList,contactsText,LinearLayout.class.getName());
        UiObject locationSwitch =
                findObjectByRelative(permissionList,locationText,LinearLayout.class.getName());
        UiObject phoneSwitch =
                findObjectByRelative(permissionList,phoneText,LinearLayout.class.getName());
        UiObject storageSwitch =
                findObjectByRelative(permissionList,storageText,LinearLayout.class.getName());

        //Store current permissions state of switch widgets.
        contactsSwitchState = contactSwitch.isChecked();
        locationSwitchState = locationSwitch.isChecked();
        phoneSwitchState = phoneSwitch.isChecked();
        storageSwitchState = storageSwitch.isChecked();

        //Modify application permission.
        contactSwitch.click();
        phoneSwitch.click();
        storageSwitch.click();
        locationSwitch.clickAndWaitForNewWindow();

        device.findObject(new UiSelector().textStartsWith("Deny")).clickAndWaitForNewWindow();

        //Go back two times to go to system apps page to reset permissions.
        device.pressBack();
        device.pressBack();

        //Reset app preferences from overflow menu.
        device.pressMenu();
        device.findObject(
                new UiSelector().textContains("Reset app preferences")).clickAndWaitForNewWindow();
        device.findObject(new UiSelector().textContains("RESET APPS")).clickAndWaitForNewWindow();

        //Open Maps info.
        itemList.scrollIntoView(new UiSelector().text(appName));
        itemList.getChildByText(new UiSelector().className(TextView.class.getName()), appName)
                .clickAndWaitForNewWindow();

        //Open permission and verify Contacts,Location,Phone and Storage.
        //Verify that all the permission for the app are reset.
        appInfoList.getChildByText(new UiSelector().
                className(TextView.class.getName()),"Permissions").clickAndWaitForNewWindow();

        assertEquals(contactsSwitchState,
                findObjectByRelative(
                        permissionList,"Contacts",LinearLayout.class.getName()).isChecked());
        assertEquals(locationSwitchState,
                findObjectByRelative(
                        permissionList,"Location",LinearLayout.class.getName()).isChecked());
        assertEquals(phoneSwitchState,
                findObjectByRelative(
                        permissionList,"Phone",LinearLayout.class.getName()).isChecked());
        assertEquals(storageSwitchState,
                findObjectByRelative(
                        permissionList,"Storage",LinearLayout.class.getName()).isChecked());
    }

    private UiObject findObjectByRelative(UiScrollable verticalList, String childText, String classType) throws Exception{
        UiObject uiObject = verticalList.getChildByText(new UiSelector().className(classType),childText);
        return uiObject.getChild(new UiSelector().className(Switch.class.getName()));
    }
}