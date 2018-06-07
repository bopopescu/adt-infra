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

import com.android.devtools.systemimage.uitest.utils.AccountManager;

import org.junit.Assert;

import android.support.test.uiautomator.UiDevice;
import android.support.test.uiautomator.UiSelector;
import android.support.test.uiautomator.UiWatcher;

import java.util.concurrent.TimeUnit;

/**
 * Google account login watcher.
 */
public class GoogleAccountLoginWatcher implements UiWatcher {
    private final UiDevice mDevice;
    private final String mUsername;
    private final String mPassword;

    public GoogleAccountLoginWatcher(UiDevice device, String username, String password) {
        this.mDevice = device;
        this.mUsername = username;
        this.mPassword = password;
    }

    @Override
    public boolean checkForCondition() {
        try {
            // This label is the identifier of this watcher.
            // But it takes a while to check in and load the label.
            boolean isSuccess =
                    mDevice
                            .findObject(new UiSelector().text("Add your account"))
                            .waitForExists(TimeUnit.MILLISECONDS.convert(5L, TimeUnit.SECONDS));
            if (!isSuccess) {
                return false;
            }
            AccountManager.loginGoogleAccount(mDevice, mUsername, mPassword);
            return true;
        } catch (Exception e) {
            Assert.fail(e.getStackTrace().toString());
        }
        return false;
    }
}
