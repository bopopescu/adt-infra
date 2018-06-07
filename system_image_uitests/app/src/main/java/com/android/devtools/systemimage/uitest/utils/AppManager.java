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

import com.android.devtools.systemimage.uitest.common.Res;

import android.app.Instrumentation;
import android.content.Context;
import android.content.Intent;
import android.content.res.AssetManager;
import android.net.Uri;
import android.os.Environment;
import android.support.test.uiautomator.UiDevice;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiObjectNotFoundException;
import android.support.test.uiautomator.UiScrollable;
import android.support.test.uiautomator.UiSelector;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

import junit.framework.Assert;

public class AppManager {

    private AppManager() {
        throw new AssertionError();
    }

    private static boolean isExternalStorageAvailable() {
        String extStorageState = Environment.getExternalStorageState();
        if (Environment.MEDIA_MOUNTED.equals(extStorageState)) {
            return true;
        }
        return false;
    }

    /**
     * Installs a testing app. The app must be in main/assets.
     * <p>
     * Since all APK installation and uninstallation under tests will be handled in boot strap,
     * this method will be deprecated.
     * @param instrumentation see {@link android.test.InstrumentationTestCase#getInstrumentation()
     *                        getInstrumentation}
     * @param apkName         the APK file full name in main/assets
     * @throws IOException               if File IO fails.
     * @throws UiObjectNotFoundException if it fails to find a UI widget.
     */
    @Deprecated
    public static void deprecateInstallApp(Instrumentation instrumentation, String apkName)
            throws IOException, UiObjectNotFoundException {
        Context context = instrumentation.getTargetContext();
        AssetManager assetManager = context.getAssets();
        InputStream in = assetManager.open(apkName);
        File apkFile = new File(context.getExternalFilesDir(null), apkName);
        OutputStream out = new FileOutputStream(apkFile);
        copyFile(in, out);
        in.close();
        out.close();

        // Install app via Intent and UiAutomator
        Intent intent = new Intent(Intent.ACTION_VIEW);
        intent.setDataAndType(Uri.fromFile(apkFile), "application/vnd.android.package-archive");
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        context.startActivity(intent);
        UiDevice device = UiDevice.getInstance(instrumentation);
        UiObject installButton =
                device.findObject(new UiSelector().textMatches("(INSTALL|Install)"));
        installButton.clickAndWaitForNewWindow();
        while (installButton.exists()) {
            installButton.clickAndWaitForNewWindow();
        }
        device.findObject(new UiSelector().textMatches("(DONE|Done)")).click();
    }

    @Deprecated
    private static void copyFile(InputStream in, OutputStream out) throws IOException {
        byte[] buffer = new byte[1024];
        int read;
        while ((read = in.read(buffer)) != -1) {
            out.write(buffer, 0, read);
        }
    }

    /**
     * Uninstalls a testing app.
     * <p>
     * Since all APK installation and uninstallation under tests will be handled in boot strap,
     * this method will be deprecated.
     * @param instrumentation see {@link android.test.InstrumentationTestCase#getInstrumentation()
     *                        getInstrumentation}
     * @param appName         the app name
     * @param pkgName         the app's package name which is used when the app (e.g., service) has
     *                        no name.
     * @throws Exception      if it fails to find a UI object.
     */
    @Deprecated
    public static void deprecateUninstallApp(Instrumentation instrumentation, String appName, String pkgName)
            throws Exception {
        UiDevice device = UiDevice.getInstance(instrumentation);

        // Find and click "appName" or "pkgName" in Settings/Apps
        openAppList(instrumentation);
        UiScrollable appList =
                new UiScrollable(new UiSelector().resourceIdMatches(Res.APPS_LIST_CONTAINER_RES));
        appList.setAsVerticalList();
        String searchedName;
        if (appName != null) {
            searchedName = appName;
        } else {
            if (pkgName == null) {
                throw new AssertionError("Neither appName nor pkgName is non-null.");
            }
            searchedName = pkgName;
        }
        UiObject app =
                appList.getChildByText(
                        new UiSelector().className("android.widget.TextView"),
                        searchedName
                );
        app.clickAndWaitForNewWindow();

        // Uninstall
        device.findObject(new UiSelector().text("Uninstall")).clickAndWaitForNewWindow();
        device.findObject(new UiSelector().text("OK")).clickAndWaitForNewWindow();
    }

    /**
     * Checks if an app is installed.
     *
     * @param instrumentation see {@link android.test.InstrumentationTestCase#getInstrumentation()
     *                        getInstrumentation}
     * @param appName         the app name
     * @param pkgName         the app's package name which is used when the app (e.g., service) has
     *                        no name.
     * @return {@code true} if the app is installed, or {@code false} otherwise.
     */
    public static boolean isAppInstalled(
            Instrumentation instrumentation, String appName, String pkgName)
            throws Exception {

        // Looking for "appName" or "pkgName" in Settings/Apps
        openAppList(instrumentation);
        UiScrollable appList =
                new UiScrollable(new UiSelector().resourceIdMatches(Res.APPS_LIST_CONTAINER_RES));
        appList.setAsVerticalList();
        String searchedName;
        if (appName != null) {
            searchedName = appName;
        } else {
            if (pkgName == null) {
                throw new AssertionError("Neither appName nor pkgName is non-null.");
            }
            searchedName = pkgName;
        }
        try {
            appList.getChildByText(
                    new UiSelector().className("android.widget.TextView"),
                    searchedName
            );
            return true;
        } catch (UiObjectNotFoundException e) {
            return false;
        }
    }

    /**
     * Clicks "Settings" and "Apps" options to launch the "Apps" page.
     *
     * @param instrumentation see {@link android.test.InstrumentationTestCase#getInstrumentation()
     *                        getInstrumentation}
     *
     * @throws Exception if it fails to find a UI widget.
     */
    private static void openAppList(Instrumentation instrumentation) throws Exception {
        final UiDevice device = UiDevice.getInstance(instrumentation);

        if (SystemUtil.getApiLevel() >= 26) {
            SettingsUtil.openItem(instrumentation, "Apps & notifications");
            final UiObject appInfoLabel = device.findObject(new UiSelector().textStartsWith("App info"));
            final UiObject seeAllLabel = device.findObject(new UiSelector().textStartsWith("See all"));

            boolean appInfoLabelFound = new Wait().until(new Wait.ExpectedCondition() {
                @Override
                public boolean isTrue() {
                    return appInfoLabel.exists();
                }
            });

            if (appInfoLabelFound) {
                appInfoLabel.clickAndWaitForNewWindow();
            } else {
                boolean seeAllLabelFound = new Wait().until(new Wait.ExpectedCondition() {
                    @Override
                    public boolean isTrue() {
                        return seeAllLabel.exists();
                    }
                });

                if (seeAllLabelFound) {
                    seeAllLabel.clickAndWaitForNewWindow();
                }
            }
            Assert.assertTrue("Application info not found",
                    appInfoLabel.exists() || seeAllLabel.exists());
        } else {
            SettingsUtil.openItem(instrumentation, "Apps");
        }
    }

    /**
     * Show all the system apps.
     * For API >= 23, clicks "Show system" text option from the "More options" drop down,
     * for APIs <= 22 scrolls to the last tab to select the "All" option.
     *
     * @param instrumentation see {@link android.test.InstrumentationTestCase#getInstrumentation()
     *                        getInstrumentation}
     * @throws Exception if it fails to find a UI widget.
     */
    public static void openSystemAppList(Instrumentation instrumentation) throws Exception {
        UiDevice device = UiDevice.getInstance(instrumentation);

        // Launch the "Apps" page.
        openAppList(instrumentation);

        if (SystemUtil.getApiLevel() > 22) {
            // From "More options" drop down click "Show system"
            device.pressMenu();
            device.findObject(new UiSelector().textContains("Show system")).click();
        } else {
            // Scroll to the last tab for all the system apps for APIs <= 22
            UiScrollable itemList =
                    new UiScrollable(new UiSelector().resourceId(Res.APPS_TAB_CONTAINER_RES));
            itemList.setAsHorizontalList();
            itemList.getChildByText(new UiSelector().className("android.widget.TextView"),
                    "All").clickAndWaitForNewWindow();
        }
    }
}
