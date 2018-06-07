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

import android.app.Instrumentation;
import android.support.test.uiautomator.UiDevice;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiObjectNotFoundException;
import android.support.test.uiautomator.UiScrollable;
import android.support.test.uiautomator.UiSelector;
import android.util.Log;

/**
 * Application launcher.
 */
public class AppLauncher {
    private final static String TAG = "AppLauncher";

    private AppLauncher() {
        throw new AssertionError();
    }

    /**
     * Launches application by launcher.
     *
     * @param instrumentation see {@link android.test.InstrumentationTestCase#getInstrumentation()
     *                        getInstrumentation}
     * @param appName         the app name to launch
     * @throws UiObjectNotFoundException if it fails to find a UI object.
     */
    public static void launch(Instrumentation instrumentation, String appName) throws Exception {
        UiDevice device = UiDevice.getInstance(instrumentation);
        device.pressHome();

        final UiObject appsLabel = device.findObject(new UiSelector().descriptionContains("Apps"));
        boolean appsLabelFound = false;
        boolean appNameFound;

        try {
            appsLabelFound = new Wait().until(new Wait.ExpectedCondition() {
                @Override
                public boolean isTrue() {
                    return appsLabel.exists();
                }
            });
        } catch(Exception error) {
            Log.e(TAG, error.getMessage());
            Log.e(TAG,"Launch: Apps label not found on first attempt");
        }

        if (appsLabelFound) {
            appsLabel.clickAndWaitForNewWindow();
        }

        // Attempt to scroll through the list twice, first vertically, and then horizontally.
        // If the target object cannot be found while scrolling, fling forward by a
        // maximum of 5 swipes. The combination of these techniques is intended to mediate
        // against any gesture-based failures, which can occur due to UI changes between APIs.

        final UiScrollable scrollable = new UiScrollable(new UiSelector().scrollable(true)).setAsVerticalList();
        final UiSelector appSelector = new UiSelector().text(appName);
        final UiObject app = device.findObject(appSelector);

        try {
            scrollable.setAsVerticalList();
            appNameFound = new Wait().until(new Wait.ExpectedCondition() {
                @Override
                public boolean isTrue() throws UiObjectNotFoundException {
                    return scrollable.scrollIntoView(appSelector);
                }
            });

            if (!appNameFound) {
                scrollable.setAsHorizontalList();
                appNameFound = new Wait().until(new Wait.ExpectedCondition() {
                    @Override
                    public boolean isTrue() throws UiObjectNotFoundException {
                        return scrollable.scrollIntoView(appSelector);
                    }
                });
            }
        } catch (UiObjectNotFoundException e) {
            device.pressHome();
            try {
                appsLabelFound = new Wait().until(new Wait.ExpectedCondition() {
                    @Override
                    public boolean isTrue() {
                        return appsLabel.exists();
                    }
                });
            } catch(Exception error) {
                Log.e(TAG, error.getMessage());
                Log.e(TAG,"Launch: Apps label not found on second attempt");
            }

            if (appsLabelFound) {
                appsLabel.clickAndWaitForNewWindow();
            }

            if (!app.exists()) {
                final UiObject launcherList = device.findObject(new UiSelector().
                        resourceId(Res.LAUNCHER_LIST_CONTAINER_RES));
                boolean launcherListFound = new Wait().until(new Wait.ExpectedCondition() {
                    @Override
                    public boolean isTrue() {
                        return launcherList.exists();
                    }
                });
                if (launcherListFound) {
                    launcherList.clickAndWaitForNewWindow();
                } else if (scrollable.exists()) {
                    scrollable.flingForward();
                }
            }

            appNameFound = new Wait().until(new Wait.ExpectedCondition() {
                @Override
                public boolean isTrue() {
                    return app.exists();
                }
            });
        }
        if (appNameFound) {
            app.clickAndWaitForNewWindow();
        }
    }

    /**
     * Launches application in a specific path.
     *
     * @param instrumentation see {@link android.test.InstrumentationTestCase#getInstrumentation()
     *                        getInstrumentation}
     * @param appPath         the app path to launch
     * @throws Exception if it fails to find a UI object.
     */
    public static void launchPath(Instrumentation instrumentation, String... appPath)
            throws Exception {
        final UiDevice device = UiDevice.getInstance(instrumentation);
        launch(instrumentation, appPath[0]);

        for (int i = 1; i < appPath.length; ++i) {
            UiSelector regexSelector = new UiSelector().textMatches(appPath[i]);
            UiSelector textSelector = new UiSelector().textContains(appPath[i]);

            UiObject target = device.findObject(regexSelector);
            try {
                UiScrollable scrollable = new UiScrollable(new UiSelector().scrollable(true));
                boolean isFound = scrollable.scrollIntoView(regexSelector);
                if (!isFound) {
                    target = device.findObject(textSelector);
                    scrollable.scrollIntoView(textSelector);
                }
            }
            catch (UiObjectNotFoundException e) {
                Log.e(TAG, e.getMessage());
            }
            target.clickAndWaitForNewWindow();
        }
    }
}