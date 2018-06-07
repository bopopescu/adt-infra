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

import com.android.devtools.server.model.Result;
import com.android.devtools.server.services.ServiceLocator;
import com.android.devtools.server.utils.ErrorHandleUtils;
import com.google.gson.Gson;

import java.io.IOException;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

/**
 * Handle all HTTP POST request and response.
 */
public class PostProcessor implements HttpMethodsProcessor {

  private final HttpServletRequest req;
  private final HttpServletResponse resp;

  public PostProcessor(HttpServletRequest req, HttpServletResponse resp) {
    this.req = req;
    this.resp = resp;
  }

  @Override
  public void processRequest() {
    assert req.getMethod().equals("POST");
    resp.setContentType("application/json");
    StringBuilder reqBody = new StringBuilder();
    try {
      consumeRequestBody(reqBody);
    } catch (IOException e) {
      ErrorHandleUtils.logStacktrace(ErrorHandleUtils.getStacktrace(e), "POST");
    }
    String stacktrace = null;
    try {
      resp.getWriter().print(
          ServiceLocator.getService(req.getRequestURI().substring(1)).execute(reqBody.toString()));
    } catch (Exception e) {
      stacktrace = ErrorHandleUtils.getStacktrace(e);
      ErrorHandleUtils.logStacktrace(stacktrace, "POST");
    } finally {
      try {
        if (null != stacktrace) {
          resp.getWriter().print(new Gson()
              .toJson(new Result().setIsFail(true).setDescription(stacktrace)));
        }
        resp.getWriter().flush();
        resp.getWriter().close();
      } catch (IOException e) {
        ErrorHandleUtils.logStacktrace(ErrorHandleUtils.getStacktrace(e), "POST");
      }
    }
  }

  private void consumeRequestBody(StringBuilder reqBody) throws IOException {
    String line;
    while (null != (line = req.getReader().readLine())) {
      reqBody.append(line);
    }
  }
}
