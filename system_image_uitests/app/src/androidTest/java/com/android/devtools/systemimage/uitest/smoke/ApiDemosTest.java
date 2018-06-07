/*
 * Copyright (c) 2017 The Android Open Source Project
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

package com.android.devtools.systemimage.uitest.smoke;

import android.app.Instrumentation;
import android.support.test.runner.AndroidJUnit4;
import android.support.test.uiautomator.UiDevice;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiScrollable;
import android.support.test.uiautomator.UiSelector;

import com.android.devtools.systemimage.uitest.annotations.TestInfo;
import com.android.devtools.systemimage.uitest.common.Res;
import com.android.devtools.systemimage.uitest.framework.SystemImageTestFramework;
import com.android.devtools.systemimage.uitest.utils.ApiDemosInstaller;
import com.android.devtools.systemimage.uitest.utils.AppLauncher;
import com.android.devtools.systemimage.uitest.utils.PackageInstallationUtil;
import com.android.devtools.systemimage.uitest.utils.SettingsUtil;
import com.android.devtools.systemimage.uitest.utils.Wait;
import com.android.devtools.systemimage.uitest.watchers.ApiDemosWatcher;
import junit.framework.Assert;

import org.junit.After;
import org.junit.Before;

import org.junit.Rule;
import org.junit.Test;
import org.junit.runner.RunWith;

import java.util.concurrent.TimeUnit;


/**
 * Test to verify the functionality of "PASSWORD CONTROLS".
 */
@RunWith(AndroidJUnit4.class)
public class ApiDemosTest {

    @Rule
    public final SystemImageTestFramework testFramework = new SystemImageTestFramework();

    private Instrumentation instrumentation = testFramework.getInstrumentation();
    private UiDevice device = testFramework.getDevice();

    @Before
    public void activateDeviceAdmin() throws Exception {
        ApiDemosInstaller.installApp(instrumentation);
    }

    /**
     * To test if the password is adhering to the conditions set in "PASSWORD QUALITY".
     * <p>
     * This is run to qualify releases. Please involve the test team in substantial changes.
     * <p>
     * TR ID: T144630615
     * <p>
     *   <pre>
     *   Test Steps:
     *   1. Goto API Demos —> App —> Device Admin —> Password quality.
     *   2. Set Password Quality fields by following following rules:
     *      Password quality: Complex Minimum.
     *      Minimum Length: 6 Minimum.
     *      Minimum Letters: 1.
     *      Minimum Numeric: 1.
     *      Minimum Lower case: 1.
     *      Minimum Upper Case: 1.
     *      Minimum Symbols: 1.
     *      Minimum non-Letters: 1.
     *   Verify:
     *   1. Settings —> Security —> Screen Lock —> Set it to Password.
     *      You are asked to set password according to rules mentioned above.
     *    </pre>
     *
     */
    @Test
    @TestInfo(id = "T144630615")
    public void testPasswordQuality() throws Exception {
        boolean isAPIDemoInstalled = PackageInstallationUtil.isPackageInstalled(instrumentation,
                "com.example.android.apis");
        if (isAPIDemoInstalled) {
            AppLauncher.launch(instrumentation, "API Demos");
            for (int i = 0; i < 5; i++) {
                device.pressBack();
            }
            AppLauncher.launch(instrumentation, "API Demos");

            UiScrollable itemList =
                    new UiScrollable(new UiSelector().resourceId(Res.ANDROID_LIST_RES));
            itemList.setAsVerticalList();
            Assert.assertTrue(itemList.exists());
            UiObject appItem = itemList.getChildByText(
                    new UiSelector().className("android.widget.TextView"), "App");
            appItem.waitForExists(TimeUnit.SECONDS.toMillis(3L));
            appItem.click();
            UiObject deviceAdminItem = itemList.getChildByText(
                    new UiSelector().className("android.widget.TextView"), "Device Admin");
            deviceAdminItem.waitForExists(TimeUnit.SECONDS.toMillis(3L));
            deviceAdminItem.click();
            UiObject passwordQualityItem = itemList.getChildByText(
                    new UiSelector().className("android.widget.TextView"), "Password quality");
            passwordQualityItem.waitForExists(TimeUnit.SECONDS.toMillis(3L));
            passwordQualityItem.clickAndWaitForNewWindow(3L);

            passwordQualityItem = itemList.getChildByText(
                    new UiSelector().className("android.widget.RelativeLayout"), "Password quality");
            passwordQualityItem.waitForExists(TimeUnit.SECONDS.toMillis(3L));
            passwordQualityItem.clickAndWaitForNewWindow(3L);

            // Set the criteria for password to 'Complex' type.
            device.findObject(new UiSelector().text("Complex")).clickAndWaitForNewWindow();

            // Set minimum length to 6.
            setPasswordCriteria("Minimum length", "6");

            // Set minimum letters to 1.
            setPasswordCriteria("Minimum letters", "1");

            // Set minimum numerics to 1.
            setPasswordCriteria("Minimum numeric", "1");

            // Set minimum lower case letters to 1.
            setPasswordCriteria("Minimum lower case", "1");

            // Set minimum upper case letters  to 1.
            setPasswordCriteria("Minimum upper case", "1");

            // Set minimum special symbols to 1.
            setPasswordCriteria("Minimum symbols", "1");

            // Set minimum non-letter to 1.
            setPasswordCriteria("Minimum non-letter", "1");

            //Verify that setting the password meets the "PASSWORD QUALITY" criteria.
            verifyPasswordQuality();
        }
    }

    /**
     *  Set the criteria for password.
     */
    private void setPasswordCriteria(String criteria, String value) throws Exception {
        UiScrollable itemList =
                new UiScrollable(new UiSelector().resourceId(Res.ANDROID_LIST_RES));
        itemList.setAsVerticalList();
        itemList.getChildByText(new UiSelector().className("android.widget.TextView"),
                criteria).clickAndWaitForNewWindow();
        UiObject editText = device.findObject(new UiSelector().className("android.widget.EditText"));
        editText.setText(value);
        device.findObject(new UiSelector().text("OK")).clickAndWaitForNewWindow();
    }

    /**
     *  Verify the functionality of "PASSWORD QUALITY".
     */
    private void verifyPasswordQuality() throws Exception {
        String securitySettings;

        if (testFramework.getApi() >= 27) {
            securitySettings = "Security & location";
        } else if (testFramework.getApi() == 26) {
            securitySettings = "Security & Location";
        } else {
            securitySettings = "Security";
        }

        Assert.assertTrue(SettingsUtil.openItem(instrumentation, securitySettings));

        Assert.assertTrue("Scrollable list not found",
                new Wait().until(new Wait.ExpectedCondition() {
                    @Override
                    public boolean isTrue() {
                        return device.findObject(new UiSelector().
                                resourceIdMatches(Res.SETTINGS_LIST_CONTAINER_RES)).exists();
                    }
                }));

        UiScrollable itemList =
                new UiScrollable(
                        new UiSelector().resourceIdMatches(Res.SETTINGS_LIST_CONTAINER_RES)
                );

        itemList.setAsVerticalList();

        itemList.getChildByText(new UiSelector().className("android.widget.TextView"),
                "Screen lock").clickAndWaitForNewWindow();
        itemList.getChildByText(new UiSelector().className("android.widget.TextView"),
                "Password").clickAndWaitForNewWindow();

        new ApiDemosWatcher(device).checkForCondition();
        UiObject passwordField = device.findObject(
                new UiSelector().className("android.widget.EditText"));
        passwordField.waitForExists(TimeUnit.SECONDS.toMillis(3L));

        //Assert "Minimum Length".
        validateWrongPassword("aB!1b", "Must be at least 6 characters");

        //Assert "Minimum Upper Case".
        validateWrongPassword("abc1!d", "Must contain at least 1 uppercase letter");

        //Assert "Minimum Lower Case".
        validateWrongPassword("ABC1!D", "Must contain at least 1 lowercase letter");

        //Assert "Minimum Numerical Digits".
        validateWrongPassword("AaBC!D", "Must contain at least 1 numerical digit");

        //Assert "Minimum Special Symbols".
        validateWrongPassword("AaBC1D", "Must contain at least 1 special symbol");

        //Assertion for a valid password that meets all the "PASSWORD QUALITY" criteria.
        passwordField.setText("Abc1!d");

        String continueButtonLabel;
        if (testFramework.getApi() == 27) {
            continueButtonLabel = "NEXT";
        } else {
            continueButtonLabel = "Continue";
        }
        UiObject continueButton = device.findObject(
                new UiSelector().className("android.widget.Button").textContains(continueButtonLabel));
        continueButton.waitForExists(TimeUnit.SECONDS.toMillis(3L));
        Assert.assertTrue(continueButton.isEnabled());
    }

    /**
     * Assert the wrong password value with the correct error message.
     */
    private void validateWrongPassword(String password, String errorMessage) throws Exception {
        UiObject passwordField = device.findObject(
                new UiSelector().className("android.widget.EditText"));

        passwordField.setText(password);
        UiObject passwordError = device.findObject(new UiSelector().textContains(errorMessage));
        passwordError.waitForExists(3L);
        Assert.assertTrue(passwordError.exists());
        pressDeleteKey(password.length());
    }

    /**
     * Common code to delete all the characters in the password field.
     */
    private void pressDeleteKey(int n){
        while(n > 0){
            device.pressDelete();
            n--;
        }
    }

    @After
    public void restoreState() throws Exception{
        //Deactivate "Device Admin" to restore the state.
        SettingsUtil.deactivate(instrumentation, "Sample Device Admin");
    }

}