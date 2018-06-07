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

package com.android.devtools.systemimage.uitest.watchers;


import android.support.test.uiautomator.UiDevice;
import android.support.test.uiautomator.UiObjectNotFoundException;
import android.support.test.uiautomator.UiSelector;
import android.support.test.uiautomator.UiWatcher;

import java.util.concurrent.TimeUnit;

/**
 * Camera permissions popup watcher that monitors and dismisses settings confirmation popup dialogs.
 */
public class CameraAccessPermissionsWatcher implements UiWatcher {
    private final UiDevice mDevice;

    public CameraAccessPermissionsWatcher(UiDevice device) {
        this.mDevice = device;
    }

    @Override
    public boolean checkForCondition() {
        boolean condition = false;
        boolean hasPopup =
                mDevice.findObject(new UiSelector().textMatches("(?i)allow(?-i)"))
                        .waitForExists(TimeUnit.MILLISECONDS.convert(3L, TimeUnit.SECONDS));
        try {
            if (hasPopup) {
                mDevice.findObject(new UiSelector().textMatches("(?i)allow(?-i)")).clickAndWaitForNewWindow();
                condition = true;
            }
            hasPopup = mDevice.findObject(new UiSelector().textMatches("(?i)next(?-i)"))
                    .waitForExists(TimeUnit.MILLISECONDS.convert(3L, TimeUnit.SECONDS));
            if (hasPopup) {
                mDevice.findObject(new UiSelector().textMatches("(?i)next(?-i)")).clickAndWaitForNewWindow();
                condition = true;
            }
            hasPopup = mDevice.findObject(new UiSelector().textMatches("(?i)got it(?-i)"))
                    .waitForExists(TimeUnit.MILLISECONDS.convert(3L, TimeUnit.SECONDS));
            if (hasPopup) {
                mDevice.findObject(new UiSelector().textMatches("(?i)got it(?-i)")).clickAndWaitForNewWindow();
                condition = true;
            }
        }
        catch (UiObjectNotFoundException e) {
            throw new AssertionError("Unable to grant camera privilege");
        }
        return condition;
    }
}