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
import android.support.test.uiautomator.UiSelector;
import android.support.test.uiautomator.UiWatcher;

/**
 * Google Now welcome view watcher.
 */
public class GoogleNowWelcomeViewWatcher implements UiWatcher {
    private final UiDevice mDevice;

    public GoogleNowWelcomeViewWatcher(UiDevice device) {
        mDevice = device;
    }

    @Override
    public boolean checkForCondition() {
        UiObject skipButton = mDevice.findObject(
                new UiSelector().resourceIdMatches(Res.NOW_SIGNIN_DECLINE_BUTTON_RES));
        try {
            if (skipButton.exists()) {
                skipButton.clickAndWaitForNewWindow();
                return true;
            } else {
                return false;
            }
        } catch (Exception e) {
            Assert.fail(e.getStackTrace().toString());
            return false;
        }
    }
}
