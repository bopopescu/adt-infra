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
import android.os.Build;
import android.text.TextUtils;

/**
 * Install the ApiDemos application, based on chipset
 */
public class ApiDemosInstaller {

    private ApiDemosInstaller() {
        throw new AssertionError();
    }

    /**
     * Installs API Demos test onto image, if not present
     * @param instrumentation see {@link android.test.InstrumentationTestCase#getInstrumentation()
     * @throws UiObjectNotFoundException if it fails to find a UI object.
     */
    @TargetApi(24)
    public static void installApp(Instrumentation instrumentation)
            throws Exception {
        String testPackageName = "com.example.android.apis";
        String testPackageAPK32 = "ApiDemos_x86.apk";
        String testPackageAPK64 = "ApiDemos_x86_64.apk";

        String apk = TextUtils.join(", ", Build.SUPPORTED_ABIS).contains("64") ?
                testPackageAPK64 : testPackageAPK32;
        boolean isAPIDemoInstalled = PackageInstallationUtil.isPackageInstalled(instrumentation,
                testPackageName);

        if (!isAPIDemoInstalled)
            PackageInstallationUtil.installApk(instrumentation, apk);

        SettingsUtil.activate(instrumentation, "Sample Device Admin");
    }
}