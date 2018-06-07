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

package com.android.devtools.server.services;

import com.android.devtools.server.model.RestServiceModel;
import com.android.devtools.server.model.Result;
import com.android.devtools.server.model.OrientationManagerModel;
import com.google.gson.Gson;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;

import android.app.ActivityManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.support.test.uiautomator.UiDevice;
import android.util.Log;
import android.view.WindowManager;

/**
 * Service for getting device screen orientation information.
 */

public class OrientationManagerService implements Service {
  private static final String TAG = OrientationManagerService.class.getSimpleName();
  private final Context mContext;
  private final UiDevice mDevice;

  public OrientationManagerService(Context context, UiDevice uiDevice) {
    mContext = context;
    mDevice = uiDevice;
  }

  @Override
  public String execute(String json) throws IOException {
    boolean isSuccess = false;
    Result result = new Result();

    // Enable Display Auto Rotate.
    Settings.System.putInt( mContext.getContentResolver(), Settings.System.ACCELEROMETER_ROTATION, 1);

    // In order to get screen orientation and rotation, an application with UI
    // needs to be launched.
    try {
      this.launchApp();
    } catch (Exception e) {
      mDevice.pressHome();
      Log.e(TAG, "Failed to launch app with UI.");
      result.setIsFail(true);
      result.setDescription("Failed to launch app with UI.");
      return new Gson().toJson(result);
    }

    OrientationManagerModel orientationModel = new Gson()
        .fromJson(json, OrientationManagerModel.class);
    if (orientationModel == null) {
      Log.e(TAG, "OrientationModel is null. Invalid POST Request body: " + json);
      result.setIsFail(true);
      result.setDescription("Invalid POST Request body");
      return new Gson().toJson(result);
    }

    // Screen rotation has four values:
    // in android.view.Surface:
    //   ROTATION_0: 0
    //   ROTATION_180: 2
    //   ROTATION_270: 3
    //   ROTATION_90: 1
    final CountDownLatch latch1 = new CountDownLatch(1);
    final List<Integer> screenRotation = new ArrayList<>(1);
    new Handler(Looper.getMainLooper()).post(new Runnable() {
      @Override
      public void run() {
        int rotation = ((WindowManager) mContext.getSystemService(Context.WINDOW_SERVICE)).getDefaultDisplay().getRotation();
        screenRotation.add(rotation);
        latch1.countDown();
      }
    });
    try {
      latch1.await();
    } catch (InterruptedException e) {
      mDevice.pressHome();
      Log.e(TAG, "Failed to wait for rotation updated.");
      result.setIsFail(true);
      result.setDescription("Failed to wait for rotation updated.");
      return new Gson().toJson(result);
    }

    // Screen orientation has two common values:
    // in android.content.res.Configuration:
    //   ORIENTATION_PORTRAIT: 1
    //   ORIENTATION_LANDSCAPE: 2
    final CountDownLatch latch2 = new CountDownLatch(1);
    final List<Integer> screenOrientation = new ArrayList<>(1);
    new Handler(Looper.getMainLooper()).post(new Runnable() {
      @Override
      public void run() {
        int orientation = mContext.getResources().getConfiguration().orientation;
        screenOrientation.add(orientation);
        latch2.countDown();
      }
    });
    try {
      latch2.await();
    } catch (InterruptedException e) {
      mDevice.pressHome();
      Log.e(TAG, "Failed to wait for ORI updated.");
      result.setIsFail(true);
      result.setDescription("Failed to wait for ORI updated.");
      return new Gson().toJson(result);
    }

    result.setScreenRotation(Integer.toString(screenRotation.get(0)));
    result.setScreenOrientation(Integer.toString(screenOrientation.get(0)));
    isSuccess = true;
    result.setIsFail(!isSuccess);
    mDevice.pressHome();
    return new Gson().toJson(result);
  }

  private void launchApp() throws Exception {
    final PackageManager pm = mContext.getPackageManager();
    String packageName = "com.android.calculator2";
    Intent launchIntent = pm.getLaunchIntentForPackage(packageName);
    mContext.startActivity(launchIntent);

    // Wait for the app is running in the foreground.
    int maxTry = 3;
    for (int i = 0; i < maxTry; i++) {
      ActivityManager manager = (ActivityManager) mContext.getSystemService(mContext.ACTIVITY_SERVICE);
      List<ActivityManager.RunningTaskInfo> runningTaskInfo = manager.getRunningTasks(1);

      ComponentName componentInfo = runningTaskInfo.get(0).topActivity;
      if (componentInfo.getPackageName().equals(packageName)) {
        break;
      }
      Thread.sleep(1500);
    }
  }

  @Override
  public String toString() {
    return new Gson().toJson(new RestServiceModel(
        POST,
        "/OrientationManagerService",
        new OrientationManagerModel("String").toString()));
  }
}
