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

package com.android.devtools.systemimage.uitest.unittest.watchers;

import com.android.devtools.systemimage.uitest.annotations.TestInfo;
import com.android.devtools.systemimage.uitest.framework.SystemImageTestFramework;
import com.android.devtools.systemimage.uitest.utils.AppLauncher;
import com.android.devtools.systemimage.uitest.utils.PackageInstallationUtil;

import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.Timeout;
import org.junit.runner.RunWith;

import android.app.Instrumentation;
import android.support.test.runner.AndroidJUnit4;
import android.support.test.uiautomator.UiDevice;
import android.support.test.uiautomator.UiSelector;

/**
 * Unit test on {@link com.android.devtools.systemimage.uitest.watchers.CrashWatcher CrashWatcher}.
 * <p>
 * This unit test is expected to throw an assertion error.
 */
@RunWith(AndroidJUnit4.class)
public class CrashWatcherTest {
    @Rule
    public final SystemImageTestFramework testFramework = new SystemImageTestFramework();

    @Rule
    public Timeout globalTimeout = Timeout.seconds(60);

    @Test
    @TestInfo()
    public void testCrashWatcher() throws Exception {
        Instrumentation instrumentation = testFramework.getInstrumentation();
        UiDevice device = testFramework.getDevice();

        // Install DisplayingBitmaps, if not already present.
        if (!PackageInstallationUtil.isPackageInstalled(instrumentation,
                "com.example.android.displayingbitmaps")) {
            PackageInstallationUtil.installApk(instrumentation, "CrashExample.apk");
        }

        // CrashWatcher has been registered in SystemImageTestFramework#apply()
        // Here we only need to trigger the crash event, and expect the assertion failure.
        AppLauncher.launch(instrumentation, "DisplayingBitmaps");
        // Catch the crash by clicking an image.
        device.findObject(new UiSelector().className("android.widget.ImageView")).click();
    }
}