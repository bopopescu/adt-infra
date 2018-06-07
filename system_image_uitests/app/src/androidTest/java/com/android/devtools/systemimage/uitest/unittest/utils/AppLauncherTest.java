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

package com.android.devtools.systemimage.uitest.unittest.utils;

import com.android.devtools.systemimage.uitest.annotations.TestInfo;
import com.android.devtools.systemimage.uitest.framework.SystemImageTestFramework;
import com.android.devtools.systemimage.uitest.utils.AppLauncher;

import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.Timeout;
import org.junit.runner.RunWith;

import android.app.Instrumentation;
import android.support.test.runner.AndroidJUnit4;

/**
 * Unit test on {@link AppLauncher}.
 */
@RunWith(AndroidJUnit4.class)
public class AppLauncherTest {
    @Rule
    public final SystemImageTestFramework testFramework = new SystemImageTestFramework();

    @Rule
    public Timeout globalTimeout = Timeout.seconds(60);

    @Test
    @TestInfo()
    public void testAppLauncher() throws Exception {
        Instrumentation instrumentation = testFramework.getInstrumentation();

        // Common apps
        AppLauncher.launch(instrumentation, "Contacts");
        AppLauncher.launch(instrumentation, "Calendar");
        AppLauncher.launch(instrumentation, "Email");
        AppLauncher.launch(instrumentation, "Settings");
        // Camera App crashes in many system images.
        // So, we skip it for our unit tests and will add it back when it is fixed.
        // AppLauncher.launchByLauncher(getInstrumentation(), "Camera");

        // Developer apps
        AppLauncher.launch(instrumentation, "API Demos");
        AppLauncher.launch(instrumentation, "Custom Locale");
        AppLauncher.launch(instrumentation, "Dev Tools");
        AppLauncher.launch(instrumentation, "Gestures Builder");
        AppLauncher.launch(instrumentation, "Widget Preview");
    }
}
