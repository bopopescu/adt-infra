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
 * This popup watcher monitors and dismisses popup dialogs that could be displayed when logging
 * into a Google application, by providing an affirmative response.
 * <p>
 * This watcher will be deployed when logging the Google test user into either
 * Google Play Store or Google Chrome.
 */
public class GoogleAppConfirmationWatcher implements UiWatcher {
    private final UiDevice mDevice;

    public GoogleAppConfirmationWatcher(UiDevice device) {
        this.mDevice = device;
    }

    @Override
    public boolean checkForCondition() {
        boolean condition = false;
        boolean isSuccess = mDevice.findObject(new UiSelector().textContains("YES"))
                        .waitForExists(TimeUnit.MILLISECONDS.convert(3L, TimeUnit.SECONDS));
        try {
            if (isSuccess) {
                mDevice.findObject(new UiSelector().textContains("YES")).click();
                condition = true;
            }
            isSuccess =
                    mDevice.findObject(new UiSelector().description("ACCEPT"))
                            .waitForExists(TimeUnit.MILLISECONDS.convert(3L, TimeUnit.SECONDS));
            if (isSuccess) {
                mDevice.findObject(new UiSelector().description("ACCEPT")).click();
                condition = true;
            }
            isSuccess =
                    mDevice.findObject(new UiSelector().text("ACCEPT"))
                            .waitForExists(TimeUnit.MILLISECONDS.convert(3L, TimeUnit.SECONDS));
            if (isSuccess) {
                mDevice.findObject(new UiSelector().text("ACCEPT")).click();
                condition = true;
            }
            isSuccess =
                    mDevice.findObject(new UiSelector().description("I AGREE"))
                            .waitForExists(TimeUnit.MILLISECONDS.convert(3L, TimeUnit.SECONDS));
            if (isSuccess) {
                mDevice.findObject(new UiSelector().description("I AGREE")).click();
                condition = true;
            }
        }
        catch (UiObjectNotFoundException e) {
            throw new AssertionError("Failed to dismiss the play store confirmation popup dialogs");
        }
        return condition;
    }
}