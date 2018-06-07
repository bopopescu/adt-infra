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

import com.google.android.apps.common.testing.util.AndroidTestUtil;

import com.android.devtools.systemimage.uitest.common.Res;

import android.app.Instrumentation;
import android.support.test.uiautomator.UiDevice;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiObjectNotFoundException;
import android.support.test.uiautomator.UiSelector;
import android.util.Log;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.concurrent.TimeUnit;

public class AccountManager {

    private AccountManager() {
        throw new AssertionError();
    }

    private final static String TAG = "AccountManager";
    /**
     * Adds a Google account in settings.
     *
     * @param instrumentation see {@link android.test.InstrumentationTestCase#getInstrumentation()
     *                        getInstrumentation}
     * @param username        the Google account username
     * @param password        the Google account password
     * @throws UiObjectNotFoundException if it fails to find a UI widget.
     * @throws IOException               if it fails to find the Google account file.
     */
    public static void addGoogleAccount(
            Instrumentation instrumentation, String username, String password)
            throws UiObjectNotFoundException, IOException {
        // Read the username and password from a local file if null.
        // We recommended this way to add a Google account from the security perspective.
        // We keep these two params here only for testing purpose.
        // Note that the gaccountFilePath is under Android filesystem.
        // Use 'adb push' to upload a credential file before testing.
        if (username == null || password == null) {
            String gaccountFilePath =
                    AndroidTestUtil.getTestArg(
                            instrumentation.getContext().getContentResolver(),
                            "gaccount");
            BufferedReader br = new BufferedReader(new FileReader(gaccountFilePath));
            username = br.readLine().trim();
            password = br.readLine().trim();
            br.close();
        }

        try {
            openAccountList(instrumentation);
        } catch (Exception e) {
            Log.e(TAG, e.getMessage());
        }

        UiDevice device = UiDevice.getInstance(instrumentation);
        device.findObject(new UiSelector().text("Add account")).clickAndWaitForNewWindow();
        device.findObject(new UiSelector().text("Google")).clickAndWaitForNewWindow();

        // It takes a while to show the login page
        device
                .findObject(new UiSelector().text("Add your account"))
                .waitForExists(TimeUnit.MILLISECONDS.convert(5L, TimeUnit.SECONDS));

        loginGoogleAccount(device, username, password);
    }

    /**
     * Logins a Google account through Google play service.
     *
     * @param device   see {@link UiDevice}
     * @param username the Google account username
     * @param password the Google account password
     * @throws UiObjectNotFoundException if it fails to find a UI widget.
     */
    public static void loginGoogleAccount(UiDevice device, String username, String password)
            throws UiObjectNotFoundException {
        // Login a prepared Google account and password.
        // Many steps are quite laggy due to its networking nature.
        // Always wait until you see what you expect.
        device
                .findObject(new UiSelector().className("android.widget.EditText"))
                .clickAndWaitForNewWindow();
        device.findObject(new UiSelector().className("android.widget.EditText")).setText(username);
        device.pressEnter();
        device
                .findObject(new UiSelector().text(username))
                .waitForExists(TimeUnit.MILLISECONDS.convert(5L, TimeUnit.SECONDS));
        device
                .findObject(new UiSelector().className("android.widget.EditText"))
                .clickAndWaitForNewWindow();
        device.findObject(new UiSelector().className("android.widget.EditText")).setText(password);
        device.pressEnter();
        device
                .findObject(new UiSelector().descriptionContains("ACCEPT"))
                .waitForExists(TimeUnit.MILLISECONDS.convert(5L, TimeUnit.SECONDS));
        device.findObject(new UiSelector().descriptionContains("ACCEPT"))
                .clickAndWaitForNewWindow();
        device
                .findObject(new UiSelector().text("Google services"))
                .waitForExists(TimeUnit.MILLISECONDS.convert(5L, TimeUnit.SECONDS));
        device.pressBack();
    }

    /**
     * Removes a Google account from settings.
     *
     * @param instrumentation see {@link android.test.InstrumentationTestCase#getInstrumentation()
     *                        getInstrumentation}
     * @param username        the Google account username.
     * @throws UiObjectNotFoundException if it fails to find a UI widget.
     * @throws IOException               if it fails to find the Google account file.
     */
    public static void removeAccount(Instrumentation instrumentation, String username)
            throws UiObjectNotFoundException, IOException {
        if (username == null) {
            String gaccountFilePath =
                    AndroidTestUtil.getTestArg(
                            instrumentation.getContext().getContentResolver(),
                            "gaccount");
            BufferedReader br = new BufferedReader(new FileReader(gaccountFilePath));
            username = br.readLine().trim();
            br.close();
        }

        try {
            openAccountList(instrumentation);
        } catch (Exception e) {
            Log.e(TAG, e.getMessage());
        }

        UiDevice device = UiDevice.getInstance(instrumentation);
        // Iterate over the list to find and remove the account.
        UiSelector listViewSelector = new UiSelector().resourceId(Res.ANDROID_LIST_RES);
        int size = device.findObject(listViewSelector).getChildCount();
        for (int i = 0; i < size; i++) {
            UiObject item =
                    device.findObject(listViewSelector.childSelector(new UiSelector().index(i)));
            // Skip "add account".
            if (item.getText().equalsIgnoreCase("add account")) {
                continue;
            }
            item.clickAndWaitForNewWindow();
            UiObject usernameText = device.findObject(new UiSelector().text(username));
            if (usernameText.exists()) {
                usernameText.clickAndWaitForNewWindow();
                device.findObject(new UiSelector().description("More options"))
                        .clickAndWaitForNewWindow();
                device.findObject(new UiSelector().text("Remove account"))
                        .waitForExists(TimeUnit.MILLISECONDS.convert(3L, TimeUnit.SECONDS));
                device.findObject(new UiSelector().text("Remove account"))
                        .clickAndWaitForNewWindow();
                device.findObject(new UiSelector().text("Remove account"))
                        .clickAndWaitForNewWindow();
                return;
            }
        }
    }

    private static void openAccountList(Instrumentation instrumentation) throws Exception {
        SettingsUtil.openItem(instrumentation, "Accounts");
    }
}
