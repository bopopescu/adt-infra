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

import com.android.devtools.systemimage.uitest.common.Res;
import com.android.devtools.systemimage.uitest.watchers.NetworkUtilPopupWatcher;

import android.app.Instrumentation;
import android.content.Context;
import android.support.test.uiautomator.UiDevice;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiObjectNotFoundException;
import android.support.test.uiautomator.UiSelector;
import android.telephony.TelephonyManager;
import android.util.Log;

import com.android.devtools.systemimage.uitest.framework.SystemImageTestFramework;

import org.junit.Rule;

/**
 * Static utility methods pertaining to network status.
 */
public class NetworkUtil {
    private NetworkUtil() {
        throw new AssertionError();
    }

    private static final String TAG = "NetworkUtil";

    @Rule
    private final static SystemImageTestFramework testFramework = new SystemImageTestFramework();

    public static boolean hasCellularNetworkConnection(Instrumentation instrumentation) {
        TelephonyManager tm = (TelephonyManager) instrumentation.getContext().
                getSystemService(Context.TELEPHONY_SERVICE);
        Log.i("NetworkUtil", "Cellular network state is: " + tm.getDataState());

        return tm.getDataState() != TelephonyManager.DATA_DISCONNECTED;
    }

    public static boolean isAirplaneModeEnabled(UiDevice device) throws Exception {
        final UiObject airplaneModeIcon = testFramework.getApi() >= 24 ?
                device.findObject(new UiSelector().description("Airplane mode")) :
                device.findObject(new UiSelector().resourceId("com.android.systemui:id/airplane"));
        openExtendedNotificationsPanel(device);

        if (airplaneModeIcon.waitForExists(5L) && airplaneModeIcon.getText().toLowerCase().contains("on")) {
            return true;
        } else {
            UiObject airplaneModeView = device.findObject(new UiSelector().descriptionStartsWith(("Airplane mode")));
            return airplaneModeView.waitForExists(5L) && airplaneModeView.getContentDescription().toLowerCase().contains("on");
        }
    }

    public static void openExtendedNotificationsPanel(UiDevice device) throws UiObjectNotFoundException {
        new NetworkUtilPopupWatcher(device).checkForCondition();
        device.openNotification();
        new NetworkUtilPopupWatcher(device).checkForCondition();

        UiObject expandIndicator = device.findObject(new UiSelector().resourceId(Res.NOTIFICATION_BAR_EXPAND_RES));
        if (expandIndicator.waitForExists(5L)) {
            expandIndicator.clickAndWaitForNewWindow();
        } else {
            Log.d(TAG, "tray expander icon not found");
        }

        UiObject notificationHeader = device.findObject(new UiSelector().resourceId(Res.NOTIFICATION_BAR_HEADER_RES));
        if (notificationHeader.waitForExists(5L)) {
            notificationHeader.click();
            notificationHeader.swipeDown(3);
        } else {
            Log.d(TAG, "notification bar header not found");
        }
    }
}