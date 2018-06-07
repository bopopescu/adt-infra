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

import com.android.devtools.systemimage.uitest.common.Res;

import android.support.test.uiautomator.UiDevice;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiSelector;
import android.support.test.uiautomator.UiWatcher;

/**
 * Lock screen watcher that unlocks the device (assuming no password or puzzle)
 * if a lock screen has activated.
 */
public class LockScreenWatcher implements UiWatcher {
    private final UiDevice mDevice;

    public LockScreenWatcher(UiDevice device) {
        this.mDevice = device;
    }

    @Override
    public boolean checkForCondition() {
        UiObject unlock =
                mDevice.findObject(
                        new UiSelector()
                                .packageName("com.android.keyboard")
                                .descriptionContains("Slide area")
                );
        UiObject unlock2 =
                mDevice.findObject(
                        new UiSelector().resourceId(Res.LOCK_SCREEN_ICON_RES)
                );
        if (unlock.exists() || unlock2.exists()) {
            mDevice.pressMenu();
            return true;
        }
        return false;
    }
}
