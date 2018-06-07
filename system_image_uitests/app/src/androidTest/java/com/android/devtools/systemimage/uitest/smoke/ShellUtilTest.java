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

package com.android.devtools.systemimage.uitest.smoke;

import com.android.devtools.systemimage.uitest.annotations.TestInfo;
import com.android.devtools.systemimage.uitest.framework.SystemImageTestFramework;
import com.android.devtools.systemimage.uitest.utils.AppLauncher;
import com.android.devtools.systemimage.uitest.utils.ShellUtil;
import com.android.devtools.systemimage.uitest.utils.DeveloperOptionsManager;
import com.android.devtools.systemimage.uitest.utils.Wait;


import org.hamcrest.Matchers;
import org.junit.Assert;
import org.junit.Ignore;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.Timeout;
import org.junit.runner.RunWith;

import android.app.Instrumentation;
import android.support.test.runner.AndroidJUnit4;
import android.support.test.uiautomator.UiDevice;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiSelector;
import android.util.Log;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.concurrent.TimeUnit;


/**
 * Test on shell utility.
 */
@RunWith(AndroidJUnit4.class)
public class ShellUtilTest {
    private final String TAG = "ShellUtilTest";

    @Rule
    public final SystemImageTestFramework testFramework = new SystemImageTestFramework();

    @Rule
    public Timeout globalTimeout = Timeout.seconds(120);

    /**
     * Tests the integrity of Shell utilities.
     * <p>
     * This is run to qualify releases. Please involve the test team in substantial changes.
     * <p>
     * TR ID: C14578821
     * <p>
     *   <pre>
     *   Test Steps:
     *   1. Start the emulator.
     *   2. From the cmd line, run "adb shell ls /system/bin"
     *   Verify:
     *   Shell utilities are listed in SDK emulator image.
     *   </pre>
     */
    @Test
    @TestInfo(id = "14578821")
    public void testShellUtilIntegrity() throws Exception {
        Instrumentation instrumentation = testFramework.getInstrumentation();

        String cmd = "ls /system/bin";
        ShellUtil.ShellResult result = ShellUtil.invokeCommand(cmd);
        // Check if the cmd is executed correctly.
        Assert.assertTrue(result.stderr, result.stderr.length() == 0);

        // Verify the integrity of the shell utilities.
        InputStream inputStream = instrumentation.getTargetContext().getAssets().open("util.txt");
        BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream, "UTF-8"));
        String line;
        StringBuilder util = new StringBuilder();
        while ((line = reader.readLine()) != null) {
            util.append(line).append("\n");
        }
        Assert.assertThat("Failure: The shell util is incomplete.", result.stderr,
                Matchers.isEmptyOrNullString());
    }

    /**
     * Tests take bug report in Developer Options.
     * <p>
     * This is run to qualify releases. Please involve the test team in substantial changes.
     * <p>
     * TR ID: C14581588
     * <p>
     *   <pre>
     *   Test Steps:
     *   1. Start the emulator.
     *   2. Open Settings > Developer Options.
     *   3. Tap on "Take Bug Report"
     *   4. Click on REPORT button.
     *   Verify:
     *   Verify that a bug report is taken by checking for the png and zip file in the bugreport
     *     directory.
     *   </pre>
     */
    @Test
    @TestInfo(id = "14581588")
    public void createBugReport() throws Exception {
        Instrumentation instrumentation = testFramework.getInstrumentation();
        final UiDevice device = UiDevice.getInstance(instrumentation);
        final String BUG_REPORT_DIR;

        if (testFramework.getApi() > 23) {
            BUG_REPORT_DIR = "/bugreports";
        } else {
            BUG_REPORT_DIR = "/data/data/com.android.shell/files/bugreports";
        }

        if (testFramework.getApi() >= 21) {
            deleteBugReportFiles(BUG_REPORT_DIR);

            if (!DeveloperOptionsManager.isDeveloperOptionsEnabled(testFramework)) {
                DeveloperOptionsManager.enableDeveloperOptions(testFramework);
            }

            AppLauncher.launchPath(instrumentation, new String[] {"Settings", "System", "Developer options"});
            // Remove bug report files even if the test fails.
            try {
                device.findObject(
                        new UiSelector().text("Take bug report")).clickAndWaitForNewWindow();
                UiObject fullReportButton = device.findObject(new UiSelector().textMatches("(?i)full report(?-i)"));
                if (fullReportButton.exists()) {
                    fullReportButton.clickAndWaitForNewWindow();
                }
                UiObject reportButton = device.findObject(new UiSelector().textMatches("(?i)report(?-i)"));
                if (reportButton.exists()) {
                    reportButton.click();
                }
                boolean gotPngAndZip = new Wait(
                        TimeUnit.MILLISECONDS.convert(30L, TimeUnit.SECONDS)).until(
                        new Wait.ExpectedCondition() {
                            @Override
                            public boolean isTrue() throws Exception {
                                String result = device.executeShellCommand("ls " + BUG_REPORT_DIR);
                                Log.d(TAG, "ls result " + result);
                                boolean success =
                                        result.matches("(?s).*bugreport.*\\.png.*")
                                                && result.matches("(?s).*bugreport.*\\.zip.*");

                                return success;
                            }
                        });
                Assert.assertTrue("Missing bug report files for png and zip.", gotPngAndZip);
            } finally {
                deleteBugReportFiles(BUG_REPORT_DIR);
            }
        }
    }

    public void deleteBugReportFiles(String reportDir) throws Exception {
        Log.i(TAG, "Deleting any existing bug report files");

        Instrumentation instrumentation = testFramework.getInstrumentation();
        UiDevice device = UiDevice.getInstance(instrumentation);

        // Delete all png and zip bug reports. Delete the files one at a time, as wildcards
        // don't work.
        String lsResult = device.executeShellCommand("ls " + reportDir);
        String[] files = lsResult.split("\\s+");
        String filename = "bugreport.*\\.(png|zip)";

        for (String file : files) {
            if (file.matches(filename)) {
                device.executeShellCommand(String.format("rm %s/%s", reportDir, file));
            }
        }
    }
}
