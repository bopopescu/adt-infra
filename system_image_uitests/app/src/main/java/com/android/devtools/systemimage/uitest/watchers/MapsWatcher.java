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
 * Maps Test popup watcher that monitors and dismisses Google Maps confirmation popup dialogs.
 */
public class MapsWatcher implements UiWatcher {
    private final UiDevice mDevice;

    public MapsWatcher(UiDevice device) {
        this.mDevice = device;
    }

    @Override
    public boolean checkForCondition() {
        boolean condition = false;
        boolean isSuccess = mDevice.findObject(new UiSelector().textContains("ACCEPT & CONTINUE"))
                .waitForExists(TimeUnit.MILLISECONDS.convert(3L, TimeUnit.SECONDS));
        try {
            if (isSuccess) {
                mDevice.findObject(new UiSelector().textContains("ACCEPT & CONTINUE")).click();
                condition = true;
            }
            isSuccess = mDevice.findObject(new UiSelector().textContains("SKIP"))
                    .waitForExists(TimeUnit.MILLISECONDS.convert(3L, TimeUnit.SECONDS));
            if (isSuccess) {
                mDevice.findObject(new UiSelector().textContains("SKIP")).click();
                condition = true;
            }
            isSuccess = mDevice.findObject(new UiSelector().textContains("GOT IT"))
                    .waitForExists(TimeUnit.MILLISECONDS.convert(3L, TimeUnit.SECONDS));
            if (isSuccess) {
                mDevice.findObject(new UiSelector().textContains("GOT IT")).click();
                condition = true;
            }
            isSuccess = mDevice.findObject(new UiSelector().textContains("OK"))
                    .waitForExists(TimeUnit.MILLISECONDS.convert(3L, TimeUnit.SECONDS));
            if (isSuccess) {
                mDevice.findObject(new UiSelector().textContains("OK")).click();
                condition = true;
            }

        }
        catch (UiObjectNotFoundException e) {
            throw new AssertionError("Failed to dismiss the play store confirmation popup dialogs");
        }
        return condition;
    }
}