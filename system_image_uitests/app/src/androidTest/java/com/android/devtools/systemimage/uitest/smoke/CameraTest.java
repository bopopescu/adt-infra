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

import android.app.Instrumentation;
import android.os.Environment;
import android.support.test.runner.AndroidJUnit4;
import android.support.test.uiautomator.UiDevice;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiObjectNotFoundException;
import android.support.test.uiautomator.UiSelector;
import android.util.Log;

import com.android.devtools.systemimage.uitest.annotations.TestInfo;
import com.android.devtools.systemimage.uitest.common.Res;
import com.android.devtools.systemimage.uitest.framework.SystemImageTestFramework;
import com.android.devtools.systemimage.uitest.utils.AppLauncher;
import com.android.devtools.systemimage.uitest.utils.PackageInstallationUtil;
import com.android.devtools.systemimage.uitest.utils.ShellUtil;
import com.android.devtools.systemimage.uitest.utils.Wait;
import com.android.devtools.systemimage.uitest.watchers.CameraAccessPermissionsWatcher;

import org.junit.Assert;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.Timeout;
import org.junit.runner.RunWith;

import java.io.File;
import java.util.concurrent.TimeUnit;

import static org.junit.Assert.assertTrue;

/**
 * Test on shell utility.
 */
@RunWith(AndroidJUnit4.class)
public class CameraTest {
    private final String TAG = "CameraTest";

    @Rule
    public final SystemImageTestFramework testFramework = new SystemImageTestFramework();

    @Rule
    public Timeout globalTimeout = Timeout.seconds(120);

    final private int api = testFramework.getApi();

    /**
     * Tests the photo capture functionality of the camera application.
     * <p>
     * TT ID: ab5f9585-433b-4261-bd15-5c7136f6127b
     * <p>
     *   <pre>
     *   Test Steps:
     *   1. Start the emulator.
     *   2. Open the Camera application.
     *   3. Take a photo.
     *   4. Delete the photo.
     *   5. Get list of files stored in the Gallery.
     *   6. Reopen the Camera application.
     *   7. Take another photo.
     *   8. Get an updated list of files stored in the Gallery.
     *   9. Delete the photo.
     *   10. Get a final list of files stored in the Gallery.
     *   Verify:
     *      1. Confirm that after taking a photo, the current file list does not match the original file list,
     *          and contains a file with a .jpg extension.
     *      2. Confirm that after deleting the photo, the final file list match the original file list.
     */
    @Test
    @TestInfo(id = "ab5f9585-433b-4261-bd15-5c7136f6127b")
    public void testPhotoCapture() throws Exception {
        Instrumentation instrumentation = testFramework.getInstrumentation();

        if (api >= 24) {
            boolean photoTestSuccess = useCamera(instrumentation, "Camera");
            Assert.assertTrue("New photo was not deleted from the gallery", photoTestSuccess);
        }
    }

    /**
     * Tests the video capture functionality of the camera application.
     * <p>
     * TT ID: ab5f9585-433b-4261-bd15-5c7136f6127b
     * <p>
     *   <pre>
     *   Test Steps:
     *   1. Start the emulator.
     *   2. Open the Camera application and set to Video.
     *   3. Take a video.
     *   4. Delete the video.
     *   5. Get list of files stored in the Gallery.
     *   6. Reopen the Camera application.
     *   7. Take another video.
     *   8. Get an updated list of files stored in the Gallery.
     *   9. Delete the video.
     *   10. Get a final list of files stored in the Gallery.
     *   Verify:
     *      1. Confirm that after taking a video, the current file list does not match the original video list,
     *          and contains a file with a .mp4 extension.
     *      2. Confirm that after deleting the video, the final file list match the original video list.
     */
    @Test
    @TestInfo(id = "ab5f9585-433b-4261-bd15-5c7136f6127b")
    public void testVideoCapture() throws Exception {
        Instrumentation instrumentation = testFramework.getInstrumentation();

        if (api >= 24) {
            boolean videoTestSuccess = useCamera(instrumentation, "Video");
            Assert.assertTrue("New video was not deleted from the gallery", videoTestSuccess);
        }
    }

    /* A helper method to perform the common camera actions of both the photo and video tests,
     * based on the mode parameter */
    private boolean useCamera(Instrumentation instrumentation, String mode) throws Exception {
        final UiDevice device = UiDevice.getInstance(instrumentation);

        AppLauncher.launchPath(instrumentation, new String[]{"Camera"});
        new CameraAccessPermissionsWatcher(device).checkForCondition();

        device.pressBack();
        device.pressHome();

        AppLauncher.launchPath(instrumentation, new String[]{"Camera"});
        UiObject cameraFrame = device.findObject(new UiSelector().resourceId(Res.CAMERA_FRAME_RES));
        if (cameraFrame.waitForExists(5L)) {
            cameraFrame.click();
            cameraFrame.swipeRight(3);
        }

        new CameraAccessPermissionsWatcher(device).checkForCondition();

        boolean cameraModeButtonExists = new Wait().until(new Wait.ExpectedCondition() {
                @Override
                public boolean isTrue() {
                    return device.findObject(new UiSelector().descriptionStartsWith("Switch to")).exists();
                }
            });

        Assert.assertTrue("Button to select " + mode + " mode not found", cameraModeButtonExists);

        if (mode.equals("Camera")) {
            device.findObject(new UiSelector().description("Switch to Camera Mode")).click();
        } else {
            device.findObject(new UiSelector().description("Switch to Video Camera")).click();
        }

        createTestFile(device, mode);
        deleteTestFile(device);

        String originalFileList = listGalleryFiles(instrumentation);

        AppLauncher.launchPath(instrumentation, new String[]{"Camera"});
        new CameraAccessPermissionsWatcher(device).checkForCondition();

        createTestFile(device, mode);

        String fileExt = mode.equals("Camera") ? ".jpg" : ".mp4";
        String newFileList = listGalleryFiles(instrumentation);

        Log.d(TAG, "Test mode is " + mode);
        Log.d(TAG, "Original gallery file list is " + originalFileList);
        Log.d(TAG, "Gallery file list after create is " + newFileList);

        Assert.assertTrue("New file was not added to the gallery",
                !originalFileList.equals(newFileList) && newFileList.contains(fileExt));

        deleteTestFile(device);

        String lastFileList = listGalleryFiles(instrumentation);
        Log.d(TAG, "Gallery file list after delete is " + lastFileList);

        return originalFileList.equals(lastFileList);
    }

    /**
     * Verifies that the augmented reality application can be installed and launched
     * <p>
     * TT ID: 61ba18b5-cfba-46a7-a3f2-abfc60e40303
     * <p>
     *   <pre>
     *   Test Steps:
     *   1. Start the emulator.
     *   2. Check if AR application is installed, and install if not found.
     *   3. Open the AR application.
     *   Verify:
     *      Confirm that the application launches, and the target text is displayed
     *
     *   This test runs on API 27+ images with Google API's.
     */
    @Test
    @TestInfo(id = "61ba18b5-cfba-46a7-a3f2-abfc60e40303")
    public void launchARApp() throws Exception {
        Instrumentation instrumentation = testFramework.getInstrumentation();
        final UiDevice device = testFramework.getDevice();

        if (api < 27 || !(testFramework.isGoogleApiImage()) || testFramework.isGoogleApiAndPlayImage()) {
            return;
        }

        String testPackageName = "com.google.ar.core.examples.c.helloar";
        String apk = "HelloAr_C.apk";
        String appName = "HelloAR C";
        boolean isAPIDemoInstalled = PackageInstallationUtil.
                isPackageInstalled(instrumentation, testPackageName);

        if (!isAPIDemoInstalled) {
            PackageInstallationUtil.installApk(instrumentation, apk);
        }

        AppLauncher.launchPath(instrumentation, new String[]{appName});
        new CameraAccessPermissionsWatcher(device).checkForCondition();

        assertTrue("'Searching for surfaces...' text is not visible",
                new Wait().until(new Wait.ExpectedCondition() {
                    @Override
                    public boolean isTrue() {
                        return device.findObject(new UiSelector().resourceId(
                                Res.GOOGLE_AR_SNACKBAR_RES).text("Searching for surfaces...")).exists();
                    }
                })
        );
    }

    /* A helper method to list the contents on the external media files storage directory */
    private String listGalleryFiles(Instrumentation instrumentation) throws Exception {
        final File externalStorage = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DCIM);
        final String externalStorageDir = externalStorage.toString() + "/Camera";
        final String cmd = "ls " + externalStorageDir;

        final ShellUtil.ShellResult result = ShellUtil.invokeCommand(cmd);

        boolean photosListed = new Wait(
                TimeUnit.MILLISECONDS.convert(10L, TimeUnit.SECONDS)).until(
                    new Wait.ExpectedCondition() {
                    @Override
                    public boolean isTrue() {
                        return result.stderr != null && result.stderr.length() == 0;
                    }
                });

        if (!photosListed) {
            Log.e(TAG, "Gallery files not listed. Error: " + result.stderr);
            Log.w(TAG, "External storage directory is " + externalStorageDir);
            Log.w(TAG, "Shell command (" + cmd + ") results: " + result.stdout);
        }

        Assert.assertTrue("Media gallery 'ls' command failed.", photosListed);
        Log.d(TAG, "ls result " + result.stdout);
        return result.stdout;
    }

    /* A helper method to generate either a new photo or video, and then select view it */
    private void createTestFile(UiDevice device, String mode) throws UiObjectNotFoundException {
        UiObject shutterButton = device.findObject(new UiSelector().resourceId(Res.CAMERA_SHUTTER_BUTTON_RES));
        UiObject fileThumbnail = device.findObject(new UiSelector().resourceId(Res.CAMERA_FILE_THUMBNAIL_RES));

        if (shutterButton.waitForExists(3L)) {
            shutterButton.click();
            if (mode.equals("Video")) {
                fileThumbnail.waitForExists(3L);
                shutterButton.click();
            }

            if (fileThumbnail.waitForExists(3L)) {
                fileThumbnail.clickAndWaitForNewWindow();
            }
        }
    }

    /* A helper method to delete a new photo or video */
    private void deleteTestFile(UiDevice device) throws UiObjectNotFoundException {
        UiObject trashCan = device.findObject(new UiSelector().resourceId(Res.CAMERA_FILE_DELETE_RES));
        UiObject fileThumbnail = device.findObject(new UiSelector().resourceId(Res.CAMERA_FILE_THUMBNAIL_RES));

        if (fileThumbnail.waitForExists(3L)) {
            fileThumbnail.clickAndWaitForNewWindow();
        }

        if (trashCan.waitForExists(3L)) {
            trashCan.click();
        }

        device.pressBack();
        device.pressHome();
    }
}