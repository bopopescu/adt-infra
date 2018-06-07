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

package com.android.devtools.systemimage.uitest.utils;

import android.app.Instrumentation;
import android.support.test.uiautomator.UiDevice;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiObjectNotFoundException;
import android.support.test.uiautomator.UiScrollable;
import android.support.test.uiautomator.UiSelector;

import com.android.devtools.systemimage.uitest.common.Res;
import com.android.devtools.systemimage.uitest.watchers.GoogleAppConfirmationWatcher;

import java.util.concurrent.TimeUnit;


/**
 * Static utility methods pertaining to the Google Play Store
 */
public class PlayStoreUtil {

    private PlayStoreUtil() {
        throw new AssertionError();
    }

    private static final int api = SystemUtil.getApiLevel();

    /**
     * Checks if Play Store has been installed.
     * Returns true if Play Store has been installed, false if not.
     */
    public static boolean isPlayStoreInstalled(Instrumentation instrumentation) throws Exception {
        final UiDevice device = UiDevice.getInstance(instrumentation);
        boolean isInstalled;
        final String playStore = "Play Store";

        device.pressHome();
        if (api == 24) {
            device.findObject(new UiSelector().descriptionContains("Apps")).clickAndWaitForNewWindow();
            final UiScrollable scrollable = new UiScrollable(new UiSelector().scrollable(true));
            isInstalled = new Wait().until(new Wait.ExpectedCondition() {
                @Override
                public boolean isTrue() throws UiObjectNotFoundException {
                    scrollable.scrollIntoView(new UiSelector().text(playStore));
                    return scrollable.getChild(new UiSelector().text(playStore)).exists();
                }
            });
        } else {
            isInstalled = new Wait().until(new Wait.ExpectedCondition() {
                @Override
                public boolean isTrue() throws UiObjectNotFoundException {
                    return device.findObject(new UiSelector().text(playStore)).exists();
                }
            });
        }
        return isInstalled;
    }

    /**
     * Backtracks to the opening Play Store screen.
     */
    public static void resetPlayStore(Instrumentation instrumentation) {
        final UiDevice device = UiDevice.getInstance(instrumentation);

        for (int i = 0; i < 5; i++) {
            device.pressBack();
        }
    }

    /**
     * Launches Google Play Store, opening to the given application
     */
    public static void launchGooglePlay(Instrumentation instrumentation, String appName) throws Exception {
        final UiDevice device = UiDevice.getInstance(instrumentation);
        final String application = appName;
        AppLauncher.launch(instrumentation, "Play Store");

        resetPlayStore(instrumentation);
        AppLauncher.launch(instrumentation, "Play Store");

        boolean idleTextFieldExists = new Wait().until(new Wait.ExpectedCondition() {
            @Override
            public boolean isTrue() throws UiObjectNotFoundException {
                return device.findObject(
                        new UiSelector().resourceId(Res.GOOGLE_PLAY_IDLE_RES)).exists();
            }
        });

        if (idleTextFieldExists) {
            device.findObject(
                    new UiSelector().resourceId(Res.GOOGLE_PLAY_IDLE_RES)).click();
        }

        boolean inputTextFieldExists = new Wait().until(new Wait.ExpectedCondition() {
            @Override
            public boolean isTrue() throws UiObjectNotFoundException {
                return device.findObject(
                        new UiSelector().resourceId(Res.GOOGLE_PLAY_INPUT_RES)).exists();
            }
        });

        if (inputTextFieldExists) {
            UiObject inputTextField = device.findObject(
                    new UiSelector().resourceId(Res.GOOGLE_PLAY_INPUT_RES));
            inputTextField.clearTextField();
            inputTextField.setText(application);
            device.pressEnter();
        }
    }

    /**
     * Checks if test user is logged in to Google Play.  Logs in if not.
     */
    public static void loginGooglePlay(Instrumentation instrumentation) throws Exception {
        final UiDevice device = UiDevice.getInstance(instrumentation);
        resetPlayStore(instrumentation);
        AppLauncher.launch(instrumentation, "Play Store");
        new GoogleAppConfirmationWatcher(device).checkForCondition();

        boolean hasSearchBox = new Wait(TimeUnit.SECONDS.toMillis(5)).
                until(new Wait.ExpectedCondition() {
                    @Override
                    public boolean isTrue() throws UiObjectNotFoundException {
                        return device.findObject(
                                new UiSelector().resourceId(Res.GOOGLE_PLAY_IDLE_RES)).exists() ||
                                device.findObject(
                                        new UiSelector().resourceId(Res.GOOGLE_PLAY_ACTIVE_RES)).exists();
                    }
                });
        if (hasSearchBox) {
            device.pressHome();
            return;
        }

        GoogleAppUtil.loginGoogleApp(instrumentation);

        AppLauncher.launch(instrumentation, "Play Store");
        new GoogleAppConfirmationWatcher(device).checkForCondition();
        device.pressHome();
    }

    /**
     * Attempts to install an application from Google Play Store, if it is not already installed.
     * Returns true if the application has been installed, false if not.
     */
    public static boolean installApplication(Instrumentation instrumentation) throws Exception {
        final UiDevice device = UiDevice.getInstance(instrumentation);

        boolean isInstallable = new Wait().until(new Wait.ExpectedCondition() {
            @Override
            public boolean isTrue() throws UiObjectNotFoundException {
                return device.findObject(new UiSelector()
                        .text("INSTALL")).exists();
            }
        });

        if (!isInstallable) {
            return new Wait().until(new Wait.ExpectedCondition() {
                @Override
                public boolean isTrue() throws UiObjectNotFoundException {
                    return device.findObject(new UiSelector()
                            .text("UNINSTALL")).exists();
                }
            });
        }

        device.findObject(new UiSelector().text("INSTALL")).clickAndWaitForNewWindow();
        new GoogleAppConfirmationWatcher(device).checkForCondition();

        UiObject openButton = device.findObject(new UiSelector().text("OPEN"));
        boolean isAppInstalled = openButton.waitForExists(TimeUnit.SECONDS.toMillis(60));

        return isAppInstalled;
    }

    /**
     * Attempts to uninstall an application from Google Play Store, if it is already installed.
     * Returns true if the application has been uninstalled, false if not.
     */
    public static boolean uninstallApplication(Instrumentation instrumentation) throws Exception {
        final UiDevice device = UiDevice.getInstance(instrumentation);

        boolean isUninstallable = new Wait().until(new Wait.ExpectedCondition() {
            @Override
            public boolean isTrue() throws UiObjectNotFoundException {
                return device.findObject(new UiSelector()
                        .text("UNINSTALL")).exists();
            }
        });

        if (!isUninstallable) {
            return new Wait().until(new Wait.ExpectedCondition() {
                @Override
                public boolean isTrue() throws UiObjectNotFoundException {
                    return device.findObject(new UiSelector()
                            .text("INSTALL")).exists();
                }
            });
        }

        device.findObject(new UiSelector().text("UNINSTALL")).clickAndWaitForNewWindow();
        device.findObject(new UiSelector().text("OK")).clickAndWaitForNewWindow();

        UiObject installButton = device.findObject(new UiSelector().text("INSTALL"));
        boolean isAppUninstalled = installButton.waitForExists(TimeUnit.SECONDS.toMillis(60));

        return isAppUninstalled;
    }
}