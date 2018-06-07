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
package com.android.devtools.server.http;

import com.android.devtools.server.services.ServiceLocator;
import com.android.devtools.server.utils.ErrorHandleUtils;

import java.io.IOException;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

/**
 * Handle all HTTP GET request and response.
 */
public class GetProcessor implements HttpMethodsProcessor {

  private final HttpServletRequest req;
  private final HttpServletResponse resp;

  public GetProcessor(HttpServletRequest req, HttpServletResponse resp) {
    this.req = req;
    this.resp = resp;
  }

  @Override
  public void processRequest() {
    assert req.getMethod().equals("GET");
    String path = req.getRequestURI();
    resp.setStatus(HttpServletResponse.SC_OK);
    if (path.equals("/help") || path.equals("/")) {
      resp.setContentType("text/html");
      writeHelpInfoToResponse();
    } else {
      resp.setContentType("application/json");
      renderServicesResponse(path);
    }
  }

  private void renderServicesResponse(String path) {
    if (null == path) {
      return;
    }
    try {
      resp.getWriter().print(ServiceLocator.getService(path.substring(1)).execute(""));
    } catch (IOException e) {
      ErrorHandleUtils.logStacktrace(ErrorHandleUtils.getStacktrace(e), "GET");
    }
  }

  private void writeHelpInfoToResponse() {
    try {
      resp.getWriter().println(ServiceLocator.getServices());
    } catch (IOException e) {
      ErrorHandleUtils.logStacktrace(ErrorHandleUtils.getStacktrace(e), "GET");
    }
  }
}
