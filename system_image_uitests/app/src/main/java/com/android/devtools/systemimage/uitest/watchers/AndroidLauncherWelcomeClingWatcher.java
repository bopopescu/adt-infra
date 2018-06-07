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

import org.junit.Assert;

import android.support.test.uiautomator.UiDevice;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiObjectNotFoundException;
import android.support.test.uiautomator.UiSelector;
import android.support.test.uiautomator.UiWatcher;

/**
 * Android launcher welcome cling watcher that dismisses a welcome cling
 * when opening launcher for the first time.
 * <p>
 * This watcher should cover all kinds of cling, overlay, popup, etc. that show just after clicking
 * the launcher for the first time. Because a dismissing button has a very general text like "OK"
 * and a watcher could be triggered at any time during a test, we should avoid using text to
 * identify a dismissing button. Instead, we should use resource ID regex.
 */
public class AndroidLauncherWelcomeClingWatcher implements UiWatcher {
    private final UiDevice mDevice;

    public AndroidLauncherWelcomeClingWatcher(UiDevice device) {
        mDevice = device;
    }

    @Override
    public boolean checkForCondition() {
        UiObject launcherCling = mDevice.findObject(
                new UiSelector().resourceIdMatches(Res.ANDROID_LAUNCHER_WELCOME_CLING_RES));
        try {
            if (launcherCling.exists()) {
                launcherCling.click();
                return true;
            } else {
                return false;
            }
        } catch (UiObjectNotFoundException e) {
            Assert.fail(e.getStackTrace().toString());
            return false;
        }
    }

}
