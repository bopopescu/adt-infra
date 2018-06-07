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

import android.app.Instrumentation;
import android.support.test.uiautomator.UiDevice;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiObjectNotFoundException;
import android.support.test.uiautomator.UiSelector;

import com.android.devtools.systemimage.uitest.common.Res;
import com.android.devtools.systemimage.uitest.watchers.GoogleAppConfirmationWatcher;

import java.util.concurrent.TimeUnit;

/**
 * Static utility method pertaining to Google Apps
 */
public class GoogleAppUtil {

    private GoogleAppUtil() {
        throw new AssertionError();
    }

    private static final int api = SystemUtil.getApiLevel();
    private static final String email = "pstester1980@gmail.com";
    private static final String password = "pst4lif3";

    /**
     * Log a user into a Google application
     */
    public static void loginGoogleApp(Instrumentation instrumentation) throws Exception {
        final UiDevice device = UiDevice.getInstance(instrumentation);
        final UiObject signInButton = device.findObject(
                new UiSelector().textMatches(("(?i)sign in(?-i)")));
        boolean needsSignIn = new Wait().
                until(new Wait.ExpectedCondition() {
                    @Override
                    public boolean isTrue() throws UiObjectNotFoundException {
                        return signInButton.exists();
                    }
                });
        if (needsSignIn) {
            signInButton.clickAndWaitForNewWindow();
        }

        String emailStr = "Email or phone";
        final UiObject inputEmailField = api == 24 ?
                device.findObject(new UiSelector().description(emailStr)) :
                device.findObject(new UiSelector().text(emailStr));

        boolean needsEmail = inputEmailField.waitForExists(
                TimeUnit.MILLISECONDS.convert(3L, TimeUnit.SECONDS));

        if (needsEmail) {
            inputEmailField.clearTextField();
            inputEmailField.setText(email);
            clickNext(device);
        }

        final UiObject inputPasswordField = api == 24 ?
                device.findObject(new UiSelector().resourceId("password")) :
                device.findObject(new UiSelector().text("Enter your password"));

        boolean needsPassword = new Wait().
                until(new Wait.ExpectedCondition() {
                    @Override
                    public boolean isTrue() {
                        return inputPasswordField.exists();
                    }
                });

        if (needsPassword) {
            inputPasswordField.clearTextField();
            inputPasswordField.setText(password);
            clickNext(device);
        }

        new GoogleAppConfirmationWatcher(device).checkForCondition();
        UiObject signInConsentAgreeButton = device.findObject(new UiSelector().resourceId(Res.NOW_SIGNIN_ACCEPT_BUTTON_RES));

        if (signInConsentAgreeButton.waitForExists(TimeUnit.MILLISECONDS.convert(3L, TimeUnit.SECONDS))) {
            signInConsentAgreeButton.clickAndWaitForNewWindow();
        }

        UiObject backupSwitch = device.findObject(new UiSelector().resourceId(Res.GOOGLE_BACKUP_SWITCH_RES));
        if (backupSwitch.waitForExists(TimeUnit.MILLISECONDS.convert(3L, TimeUnit.SECONDS))) {
            backupSwitch.clickAndWaitForNewWindow();
        }

        UiObject backupButton = device.findObject(new UiSelector().text("AGREE"));
        if (backupButton.waitForExists(TimeUnit.MILLISECONDS.convert(3L, TimeUnit.SECONDS))) {
            backupButton.clickAndWaitForNewWindow();
        }

        device.pressHome();
    }

    private static void clickNext(UiDevice device) throws UiObjectNotFoundException{
        UiObject nextButton = device.findObject(new UiSelector().text("NEXT"));
        if (!nextButton.waitForExists(TimeUnit.MILLISECONDS.convert(3L, TimeUnit.SECONDS))) {
            nextButton = device.findObject(new UiSelector().description("NEXT"));
        }

        if (nextButton.waitForExists(TimeUnit.MILLISECONDS.convert(3L, TimeUnit.SECONDS))) {
            nextButton.clickAndWaitForNewWindow();
        }
    }
}