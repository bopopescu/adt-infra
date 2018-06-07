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

package com.android.devtools.server;

import com.android.devtools.server.http.HttpServer;
import com.android.devtools.server.http.UiAutomatorServlet;
import com.android.devtools.server.services.GeoManagerService;
import com.android.devtools.server.services.OrientationManagerService;
import com.android.devtools.server.services.ServiceLocator;
import com.android.devtools.server.services.SmsManagerService;
import com.android.devtools.server.services.TelephonyManagerService;

import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;

import android.app.Instrumentation;
import android.content.Context;
import android.os.RemoteException;
import android.support.test.InstrumentationRegistry;
import android.support.test.runner.AndroidJUnit4;
import android.support.test.uiautomator.By;
import android.support.test.uiautomator.UiDevice;
import android.support.test.uiautomator.Until;
import android.util.Log;
import java.util.HashMap;
import java.util.Map;

/**
 * InstrumentationTestCase for launching servlet on emulator and use Android SDK.
 */
@RunWith(AndroidJUnit4.class)
public class Server {
  private final Instrumentation mInstrumentation =
          InstrumentationRegistry.getInstrumentation();
  private final UiDevice mDevice = UiDevice.getInstance(mInstrumentation);
  private final Context mContext = mInstrumentation.getTargetContext();

  @Before
  public void setUp() throws RemoteException {
    if (!mDevice.isScreenOn()) {
      mDevice.wakeUp();
      mDevice.wait(Until.hasObject(By.res("android", "glow_pad_view")), 10000);
      mDevice.swipe(560, 1500, 560, 1000, 40);
    }
    mDevice.pressHome();
  }

  @Test
  public void testLaunchTestServer() {
    Map<Class<?>, String> servletUrlMapping = new HashMap<>(1);
    servletUrlMapping.put(UiAutomatorServlet.class, "/");
    HttpServer server =
        new HttpServer.HttpServerBuilder()
            .withServer(new org.mortbay.jetty.Server())
            .withAcceptors(10)
            .withMaxIdleTime(1000)
            .withPort(8081)
            .withSoLingerTime(-1)
            .withServletUrlPathMapping(servletUrlMapping)
            .build();
    registerService();
    try {
      server.start();
    } catch (Exception e) {
      Log.e(this.getClass().getName(), e.getMessage());
    }
  }

  private void registerService() {
    ServiceLocator.register(new TelephonyManagerService(mContext));
    ServiceLocator.register(new SmsManagerService(mContext));
    ServiceLocator.register(new OrientationManagerService(mContext, mDevice));
    ServiceLocator.register(new GeoManagerService(mContext, mDevice));
  }
}
