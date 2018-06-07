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
 * Play Store popup watcher that monitors and dismisses Google Play Store permissions popup dialogs.
 * <p>
 * Note that this watcher should only be registered before using the Google Play Store app.
 */
public class PlayStoreControlsWatcher implements UiWatcher {
    private final UiDevice mDevice;

    public PlayStoreControlsWatcher(UiDevice device) {
        this.mDevice = device;
    }

    @Override
    public boolean checkForCondition() {
        boolean condition = false;
        boolean isSuccess =
                mDevice.findObject(new UiSelector().text("OK"))
                        .waitForExists(TimeUnit.MILLISECONDS.convert(10L, TimeUnit.SECONDS));
        try {
            if (isSuccess) {
                mDevice.findObject(new UiSelector().text("OK")).click();
                condition = true;
            }
            isSuccess =
                    mDevice.findObject(new UiSelector().text("SAVE"))
                            .waitForExists(TimeUnit.MILLISECONDS.convert(10L, TimeUnit.SECONDS));
            if (isSuccess) {
                mDevice.findObject(new UiSelector().text("SAVE")).click();
                condition = true;
            }
        } catch (UiObjectNotFoundException e) {
            throw new AssertionError("Failed to dismiss the play store permissions dialogs");
        }
        return condition;
    }
}