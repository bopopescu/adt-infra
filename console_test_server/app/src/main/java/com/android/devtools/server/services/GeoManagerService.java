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

import com.android.devtools.server.model.GeoManagerModel;
import com.android.devtools.server.model.RestServiceModel;
import com.android.devtools.server.model.Result;
import com.android.devtools.server.utils.Constants;
import com.google.gson.Gson;

import java.io.IOException;
import java.util.List;

import android.app.ActivityManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.location.Location;
import android.location.LocationManager;
import android.support.test.uiautomator.UiDevice;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiObjectNotFoundException;
import android.support.test.uiautomator.UiSelector;
import android.util.Log;


/**
 * Service for getting geo information.
 */

public class GeoManagerService implements Service {
  private static final String ACCEPT_AND_CONTINUE =
          "(?i:.*ACCEPT & CONTINUE.*)";
  private static final String GOOGLE_MAPS = "Maps";
  private static final String GPS_PROVIDER = "gps";
  private static final String IMAGE_VIEW_CLASS_NAME =
          "android.widget.ImageView";
  private static final String SKIP_LOGIN = "Skip";
  // This resouce id is only for API 23 & 24 & 25.
  private static final String LOCATION_BUTTON_R_ID_23 =
          "com.google.android.apps.gmm:id/mylocation_button";
  private static final String LOCATION_BUTTON_R_ID_24_25 =
          "com.google.android.apps.maps:id/mylocation_button";
  private static final String TAG = GeoManagerService.class.getSimpleName();

  private final Context mContext;
  private final UiDevice mDevice;

  public GeoManagerService(Context context, UiDevice uiDevice) {
    mContext = context;
    mDevice = uiDevice;
  }

  @Override
  public String execute(String json) throws IOException {
    boolean isSuccess = false;
    Result result = new Result();

    Log.d(TAG, "json = [" + json + "]");
    Log.d(TAG, "{} json payload is to get geo information.");

    if (json.equals("{}")) { // '{}' is the payload to get last know geo info.
      GeoManagerModel geoModel = new Gson().fromJson(json,
              GeoManagerModel.class);
      if (geoModel == null) {
        Log.e(TAG, "geoModel is null. Invalid POST Request body: " + json);
        result.setIsFail(true);
        result.setDescription("Invalid POST Request body");
        return new Gson().toJson(result);
      }

      LocationManager locationManager = (LocationManager)
              mContext.getSystemService(Context.LOCATION_SERVICE);
      Log.d(TAG, "locationManager = " + locationManager.toString());
      Location location = locationManager.getLastKnownLocation(GPS_PROVIDER);
      Log.d(TAG, "location = " + location.toString());

      result.setLongitude(Integer.toString((int) location.getLongitude()));
      result.setLatitude(Integer.toString((int) location.getLatitude()));
      result.setAltitude(Integer.toString((int) location.getAltitude()));
      Log.d(TAG, "set all 3 tudes.");

      isSuccess = true;
      result.setIsFail(!isSuccess);
      mDevice.pressHome();
      Log.d(TAG, "return");
      return new Gson().toJson(result);
    } else {
      // The json value passing from geo test is like: {'api': 'xx'},
      // here we try to get the api level xx, the index is from 9 (inclusive) to 11 (exclusive).
      String apiLevel = json.substring(9, 11);
      Log.d(TAG, "For API " + apiLevel);

      Log.d(TAG, "Go to Apps window, launch " + GOOGLE_MAPS +
              " app, accpet the terms and conditions, " +
              "enable Location service, then Tap on My Location.");
      try {
        this.launchGoogleMapsApp(mDevice, Integer.parseInt(apiLevel));
      } catch (Exception e) {
        mDevice.pressHome();
        String errMsg = "Failed to launch " + GOOGLE_MAPS;
        Log.e(TAG, errMsg);
        result.setIsFail(true);
        result.setDescription(errMsg);
        return new Gson().toJson(result);
      }

      result.setIsFail(false);
      result.setDescription("Initially set a location.");
      return new Gson().toJson(result);
    }
  }

  public void launchGoogleMapsApp(UiDevice uiDevice, int apiLevel)
          throws Exception {
    final PackageManager pm = mContext.getPackageManager();
    String packageName = "com.google.android.apps.maps";
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

    Log.d(TAG, "2.1) It's the first time to launch " + GOOGLE_MAPS +
            ", we need to accept the terms and enable location service. " +
            "Then go back to home screen.");
    try {
      uiDevice.findObject(new UiSelector().textMatches(ACCEPT_AND_CONTINUE)).
              clickAndWaitForNewWindow();
      Log.d(TAG, GOOGLE_MAPS + ": " + ACCEPT_AND_CONTINUE + " clicked.");
    } catch (UiObjectNotFoundException e) {
      Log.e(TAG, e.getMessage());
    }

    if (apiLevel == 23) {
      Log.d(TAG, "2.1.1) It's the first time to launch " + GOOGLE_MAPS +
              ", For API 23, we need to Skip login Maps.");
      try {
        uiDevice.findObject(new UiSelector().textMatches(SKIP_LOGIN)).
                clickAndWaitForNewWindow();
        Log.d(TAG, GOOGLE_MAPS + ": " + ACCEPT_AND_CONTINUE + " clicked.");
      } catch (UiObjectNotFoundException e) {
        Log.e(TAG, e.getMessage());
      }
    }

    // Enable location service.
    // The 'Location' icon neither has resource id nor text,
    // but it's parent's parent.
    // Hence, using it's parent's parent to get 'Location' item.
    String locationButtonRId;
    if (apiLevel == 23) {
      locationButtonRId = LOCATION_BUTTON_R_ID_23;
    } else if (apiLevel == 24 || apiLevel == 25) {
      locationButtonRId = LOCATION_BUTTON_R_ID_24_25;
    } else {
      Log.e(TAG, "The AVD API level is " +  Integer.toString(apiLevel) + ", skip this test.");
      return;
    }

    Log.d(TAG, "2.2) Start to enable GPS.");
    UiSelector parent = new UiSelector().resourceId(locationButtonRId);
    Log.d(TAG, "Get parent.");
    UiObject myLocationButton = uiDevice.findObject(parent.childSelector(
            new UiSelector().className(IMAGE_VIEW_CLASS_NAME)));
    if (myLocationButton.exists()) {
      Log.d(TAG, "Get myLocationButton.");
    } else {
      Log.e(TAG, "myLocationButton doesn't exit.");
    }

    myLocationButton.clickAndWaitForNewWindow();
    Log.d(TAG, "Enabled GPS.");

    try {
      uiDevice.findObject(new UiSelector().text(Constants.TIP_BUTTON_OK)).
              clickAndWaitForNewWindow();
      Log.d(TAG, "2.3) Improve location accuracy, " + Constants.TIP_BUTTON_OK + " clicked.");
    } catch (UiObjectNotFoundException e) {
      Log.e(TAG, e.getMessage());
    }

    // fix current location
    UiSelector ppFrameLoayout = new UiSelector().resourceId(locationButtonRId);

    UiSelector pFrameLoayout = ppFrameLoayout.index(0);
    Log.d(TAG, "get pFrameLoayout.");

    UiObject currentLocationButton = uiDevice.findObject(
            pFrameLoayout.childSelector(
                    new UiSelector().className(IMAGE_VIEW_CLASS_NAME)));
    if (currentLocationButton.exists()) {
      Log.d(TAG, "get currentLocationButton.");
    } else {
      Log.e(TAG, "currentLocationButton doesn't exit.");
    }

    currentLocationButton.clickAndWaitForNewWindow();
    Log.d(TAG, GOOGLE_MAPS + " launched.");
  }

  @Override
  public String toString() {
    return new Gson().toJson(new RestServiceModel(
        POST,
        "/GeoManagerService",
        new GeoManagerModel("String").toString()));
  }
}