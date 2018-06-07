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

import android.annotation.TargetApi;
import android.app.Instrumentation;
import android.content.Context;
import android.content.res.AssetManager;
import android.net.Uri;
import android.support.test.uiautomator.UiDevice;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiSelector;
import android.util.Log;

import com.android.devtools.systemimage.uitest.watchers.PackageInstallationUtilityWatcher;

import org.junit.Rule;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.List;
import java.util.concurrent.TimeUnit;

import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ApplicationInfo;

import com.android.devtools.systemimage.uitest.framework.SystemImageTestFramework;

/**
 * Package installation utility.
 */
public class PackageInstallationUtil {

    private PackageInstallationUtil() {
        throw new AssertionError();
    }
    private final static String TAG = "PackageInstallationUtil";

    @Rule
    public final static SystemImageTestFramework testFramework = new SystemImageTestFramework();
    /**
     * Checks if a given package is installed on the android image
     *
     * @param instrumentation see {@link android.test.InstrumentationTestCase#getInstrumentation()
     *                        getInstrumentation}
     * @param packageName     the name of the package to verify (ie com.example.android.apis)
     */
    public static boolean isPackageInstalled(Instrumentation instrumentation, String packageName) {
        Context context = testFramework.getInstrumentation().getContext();
        final PackageManager pm = context.getPackageManager();
        List<ApplicationInfo> packages = pm.getInstalledApplications(PackageManager.GET_META_DATA);

        for (ApplicationInfo packageInfo : packages) {
            if (packageInfo.packageName.contains(packageName)) {
                Log.d(TAG, packageName + " is installed.");
                return true;
            }
        }
        Log.d(TAG, packageName + " is not installed.");
        return false;
    }

    /**
     * Installs the target apk on the android image
     *
     * @param instrumentation see {@link android.test.InstrumentationTestCase#getInstrumentation()
     *                        getInstrumentation}
     * @param apkName         the name of the apk to be installed (i.e. ApiDemos_x86.apk)
     */
    @TargetApi(24)
    public static void installApk(Instrumentation instrumentation, String apkName) throws Exception {
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
        UiObject settingsButton = device.findObject(new UiSelector().textMatches("(?i)settings(?-i)"));

        boolean hasSettings = settingsButton.waitForExists(TimeUnit.MILLISECONDS.convert(3L, TimeUnit.SECONDS));
        if (hasSettings) {
            settingsButton.clickAndWaitForNewWindow();
        }

        UiObject allowSwitch = device.findObject(new UiSelector().className("android.widget.Switch"));
        boolean hasAllowSwitch = allowSwitch.waitForExists(TimeUnit.MILLISECONDS.convert(3L, TimeUnit.SECONDS));
        if (hasAllowSwitch) {
            if (allowSwitch.getText().equals("OFF")) {
                allowSwitch.click();
            }
            device.pressBack();
        } else {
            Log.w(TAG, "Could not allow installation from outside sources");
        }

        UiObject installButton = device.findObject(new UiSelector().textMatches("(?i)install(?-i)"));
        boolean hasInstallButton = installButton.waitForExists(TimeUnit.MILLISECONDS.convert(3L, TimeUnit.SECONDS));
        if (hasInstallButton) {
            installButton.clickAndWaitForNewWindow();
        }

        new PackageInstallationUtilityWatcher(device).checkForCondition();

        UiObject doneButton = device.findObject(new UiSelector().textMatches("(?i)done(?-i)"));
        boolean hasDoneButton = doneButton.waitForExists(TimeUnit.MILLISECONDS.convert(3L, TimeUnit.SECONDS));
        if (hasDoneButton) {
            doneButton.clickAndWaitForNewWindow();
        }
    }

    private static void copyFile(InputStream in, OutputStream out) throws IOException {
        byte[] buffer = new byte[1024];
        int read;
        while ((read = in.read(buffer)) != -1) {
            out.write(buffer, 0, read);
        }
    }
}
