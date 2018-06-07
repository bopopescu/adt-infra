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

import com.android.devtools.systemimage.uitest.common.Res;
import com.android.devtools.systemimage.uitest.framework.SystemImageTestFramework;

import android.app.Instrumentation;
import android.support.test.uiautomator.UiDevice;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiObjectNotFoundException;
import android.support.test.uiautomator.UiScrollable;
import android.support.test.uiautomator.UiSelector;

/**
 * Developer options manager.
 */
public class DeveloperOptionsManager {

    private DeveloperOptionsManager() {
        throw new AssertionError();
    }

    /**
     * Enables developer options.
     *
     * @param testFramework see {
     *   @link android.devtools.systemimage.uitest.framework.SystemImageTestFramework() }
     * @throws Exception if it fails to find a UI widget.
     */
    public static void enableDeveloperOptions(SystemImageTestFramework testFramework)
            throws Exception {
        Instrumentation instrumentation = testFramework.getInstrumentation();
        final UiDevice device = UiDevice.getInstance(instrumentation);

        try {
            if (testFramework.getApi() >= 26) {
                AppLauncher.launchPath(instrumentation, new String[]{"Settings", "System", "About phone"});
            } else {
                AppLauncher.launchPath(instrumentation, new String[]{"Settings", "About phone"});
            }
        } catch (UiObjectNotFoundException e) {
            if (testFramework.getApi() >= 26) {
                AppLauncher.launchPath(instrumentation, new String[]{"Settings", "System", "About emulated device"});
            } else {
                AppLauncher.launchPath(instrumentation, new String[]{"Settings", "About emulated device"});
            }
        }

        // Click "Build number"
        UiScrollable itemList =
                new UiScrollable(
                        new UiSelector().resourceIdMatches(Res.ABOUT_PHONE_LIST_CONTAINER_RES)
                );
        itemList.setAsVerticalList();
        UiObject item =
                itemList.getChildByText(
                        new UiSelector().className("android.widget.TextView"),
                        "Build number"
                );

        // Currently, UiAutomator cannot catch toast messages (see b/26511336).
        // We simply repeat for 10 times without verification. Will improve if it causes flakiness.
        for (int i = 0; i < 10; i++) {
            item.click();
        }
    }

    /**
     * Checks if the developer options is enabled.
     *
     * @param testFramework see {
     *   @link android.devtools.systemimage.uitest.framework.SystemImageTestFramework() }
     * @return {@code true} if the developer options is enabled, or {@code false} otherwise.
     * @throws Exception is it fails to find a UI widget.
     */
    public static boolean isDeveloperOptionsEnabled(SystemImageTestFramework testFramework) throws Exception {
        Instrumentation instrumentation = testFramework.getInstrumentation();
        final UiDevice device = UiDevice.getInstance(instrumentation);

        try {
            if (testFramework.getApi() >= 26) {
                SettingsUtil.openItem(instrumentation, "System");
                device.findObject(new UiSelector().text("Developer options")).click();
                return true;
            } else {
                SettingsUtil.findItem(instrumentation, "Developer options");
                return true;
            }
        } catch (UiObjectNotFoundException e) {
            return false;
        }
    }
}
