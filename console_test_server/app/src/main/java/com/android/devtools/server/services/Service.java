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

import java.io.IOException;

/**
 * Part of Service Locator design pattern, a interface for all services.
 */
public interface Service {

  static final String GET = "GET";
  static final String POST = "POST";
  static final String EMPTY_BODY = "{}";

  long MAX_WAIT_TIME = 8000;

  String execute(String json) throws IOException;
}
