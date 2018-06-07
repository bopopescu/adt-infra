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

package com.android.devtools.systemimage.uitest.framework;

import com.android.devtools.systemimage.uitest.annotations.TestInfo;
import com.android.devtools.systemimage.uitest.watchers.AndroidLauncherWelcomeClingWatcher;
import com.android.devtools.systemimage.uitest.watchers.AndroidWelcomeClingWatcher;
import com.android.devtools.systemimage.uitest.watchers.CrashWatcher;
import com.android.devtools.systemimage.uitest.watchers.LockScreenWatcher;

import org.junit.Assert;
import org.junit.rules.TestRule;
import org.junit.runner.Description;
import org.junit.runners.model.Statement;

import android.app.Instrumentation;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.os.Environment;
import android.support.test.InstrumentationRegistry;
import android.support.test.uiautomator.UiDevice;

import java.io.File;
import java.io.PrintWriter;

/**
 * System image test framework that standardizes a test's initialization and finalization.
 */
public class SystemImageTestFramework implements TestRule {

    private final Instrumentation mInstrumentation = InstrumentationRegistry.getInstrumentation();
    private final UiDevice mDevice = UiDevice.getInstance(mInstrumentation);
    private final Bundle args = InstrumentationRegistry.getArguments();
    private static final int RETRY_COUNT = 2;

    public Instrumentation getInstrumentation() {
        return mInstrumentation;
    }

    public UiDevice getDevice() {
        return mDevice;
    }

    public int getApi() {
        return Integer.parseInt(args.getString("api"));
    }

    public String getAbi() {
        return args.getString("abi");
    }

    public String getTag() {
        return args.getString("tag");
    }

    public boolean isGoogleApiImage() {
        return "google_apis".equals(getTag());
    }

    public boolean isGoogleApiAndPlayImage() {
        return "google_apis_playstore".equals(getTag());
    }

    public String getOrigin() {
        return args.getString("origin");
    }

    private boolean isExternalStorageWritable() {
        String state = Environment.getExternalStorageState();
        if (Environment.MEDIA_MOUNTED.equals(state) && !Environment.MEDIA_MOUNTED_READ_ONLY.equals(state)) {
            return true;
        }
        return false;
    }

    private boolean checkWriteExternalPermission()
    {
        String permission = "android.permission.WRITE_EXTERNAL_STORAGE";
        int res = mInstrumentation.getContext().checkCallingOrSelfPermission(permission);
        return (res == PackageManager.PERMISSION_GRANTED);
    }

    private File getLoggingDir(String testClassName, String testMethodName) {
        Assert.assertTrue("Failed to write to external storage.", isExternalStorageWritable());
        Assert.assertTrue("Failed to acquire permission.", checkWriteExternalPermission());
        File externalStorageLogDir =
                new File(Environment.getExternalStorageDirectory().getPath(), "Logs");
        if (!externalStorageLogDir.exists())
            externalStorageLogDir.mkdir();
        File loggingDir = new File(new File(externalStorageLogDir.getPath(), testClassName),
                testMethodName);
        loggingDir.mkdirs();
        return loggingDir;
    }

    @Override
    public Statement apply(final Statement base, final Description description) {
        return statement(base, description);
    }

    private Statement statement (final Statement base, final Description description) {
        return new Statement() {
            @Override
            public void evaluate() throws Throwable {
                Throwable throwable = null;

                mDevice.wakeUp();
                Assert.assertTrue("Failed to wake up the device.", mDevice.isScreenOn());
                // Press "Menu" to unlock screen if any.
                mDevice.pressMenu();
                // Press "Home" to dismiss a lock screen if any.
                mDevice.pressHome();

                CrashWatcher crashWatcher = new CrashWatcher(mDevice);
                mDevice.registerWatcher(CrashWatcher.class.getName(), crashWatcher);
                mDevice.registerWatcher(
                        LockScreenWatcher.class.getName(),
                        new LockScreenWatcher(mDevice)
                );
                mDevice.registerWatcher(
                        AndroidWelcomeClingWatcher.class.getName(),
                        new AndroidWelcomeClingWatcher(mDevice)
                );
                mDevice.registerWatcher(
                        AndroidLauncherWelcomeClingWatcher.class.getName(),
                        new AndroidLauncherWelcomeClingWatcher(mDevice)
                );
                mDevice.runWatchers();

                // Implement retry logic here
                for (int i = 0; i < RETRY_COUNT; i++) {
                    throwable = null;
                    try {
                        base.evaluate();
                        // Must check the crash watcher again for finalization,
                        // or could miss a crash if it happens at the end of a test case.
                        crashWatcher.checkForCondition();
                        mDevice.pressHome();
                    } catch (Throwable t) {
                        throwable = t;
                        File loggingDir = getLoggingDir(description.getTestClass().getSimpleName(),
                                description.getMethodName());

                        // Snap the screenshot when a test fails.
                        mDevice.takeScreenshot(new File(loggingDir, "screenshot.png"));
                        // Log the error message
                        PrintWriter error =
                                new PrintWriter(new File(loggingDir, "error.txt").getPath(), "UTF-8");
                        t.printStackTrace(error);
                        error.close();
                        // Log the test case description
                        PrintWriter info =
                                new PrintWriter(new File(loggingDir, "description.txt").getPath());
                        String testRailLink = description.getAnnotation(TestInfo.class).rootLink() +
                                description.getAnnotation(TestInfo.class).id();
                        info.println("See " + testRailLink);
                        info.println();
                        info.println("If you cannot access the link above, see http://go/adt-sysimage-autotracker instead");
                        info.close();
                    } finally {
                        mDevice.removeWatcher(CrashWatcher.class.getName());
                        mDevice.removeWatcher(LockScreenWatcher.class.getName());
                        mDevice.removeWatcher(AndroidWelcomeClingWatcher.class.getName());
                        mDevice.removeWatcher(AndroidLauncherWelcomeClingWatcher.class.getName());
                    }
                    if (throwable == null) {
                        return;
                    }
                }

                // Dismiss any left crash dialog before throw and end the test.
                // Failed to dismiss a crash dialog may impair the following tests.
                crashWatcher.dismiss();
                throw throwable;
            }
        };
    }

}
