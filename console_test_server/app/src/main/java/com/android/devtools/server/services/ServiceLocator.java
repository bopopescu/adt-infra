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
package com.android.devtools.server.services;

import android.util.Log;

import java.util.HashMap;
import java.util.Map;

/**
 * Service Locator design pattern.
 */
public final class ServiceLocator {

  private static final Map<String, Service> serviceProvider = new HashMap<>();

  public static void register(Service service) {
    serviceProvider.put(service.getClass().getSimpleName(), service);
  }

  public static Service getService(String name) {
    return serviceProvider.get(name);
  }

  public static String getServices() {
    StringBuilder sb = new StringBuilder();
    for (Service service : serviceProvider.values()){
      Log.d("hihi", service.toString());
      sb.append("<p>").append(service.toString()).append("</p>");
    }
    return sb.toString();
  }
}
