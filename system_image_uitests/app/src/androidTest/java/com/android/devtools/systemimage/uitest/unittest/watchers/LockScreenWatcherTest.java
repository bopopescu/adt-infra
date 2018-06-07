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
import com.android.devtools.systemimage.uitest.watchers.LockScreenWatcher;

import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.Timeout;
import org.junit.runner.RunWith;

import android.app.Instrumentation;
import android.support.test.runner.AndroidJUnit4;
import android.support.test.uiautomator.UiDevice;

/**
 * Unit test on {@link LockScreenWatcher}.
 */
@RunWith(AndroidJUnit4.class)
public class LockScreenWatcherTest {
    @Rule
    public final SystemImageTestFramework testFramework = new SystemImageTestFramework();

    @Rule
    public Timeout globalTimeout = Timeout.seconds(60);

    @Test
    @TestInfo()
    public void testLockScreenWatcher() throws Exception {
        Instrumentation instrumentation = testFramework.getInstrumentation();
        UiDevice device = testFramework.getDevice();

        device.registerWatcher(LockScreenWatcher.class.getName(), new LockScreenWatcher(device));
        // For some system images (e.g., API 21), sleep and wakeup can produce a lock screen.
        // Note for some other system images (e.g., API 23), there is no lock screen by default.
        device.sleep();
        device.wakeUp();
        AppLauncher.launch(instrumentation, "Email");
        device.removeWatcher(LockScreenWatcher.class.getName());
    }
}
