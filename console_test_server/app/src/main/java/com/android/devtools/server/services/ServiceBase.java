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

import com.android.devtools.server.model.Result;
import com.android.devtools.server.model.UiModel;
import com.google.gson.Gson;

import android.support.test.uiautomator.UiDevice;
import android.util.Log;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.nio.charset.Charset;

/**
 * A parent class for all services. The idea is to provide share function for all services.
 */
public abstract class ServiceBase implements Service {

  protected final UiDevice mDevice;
  protected final ByteArrayOutputStream outStream;

  protected ServiceBase(UiDevice mDevice) {
    assert null != mDevice;
    this.mDevice = mDevice;
    this.outStream = new ByteArrayOutputStream();
  }

  protected boolean isUseText(UiModel ui) {
    return null != ui.getText() && !ui.getText().isEmpty();
  }

  protected boolean isUseClass(UiModel ui) {
    return null != ui.getUiElementClass();
  }

  protected boolean isUseResourceId(UiModel ui) {
    return null != ui.getRes() && !ui.getRes().isEmpty();
  }

  protected boolean isUsingDescription(UiModel ui) {
    return null != ui.getDescription()
        && !ui.getDescription().isEmpty();
  }

  protected String getWidnowsHierachy() {
    try {
      mDevice.dumpWindowHierarchy(outStream);
    } catch (IOException e) {
      writeErrorToOutStream(e);
    }
    try {
      return outStream.toString(Charset.forName("UTF-8").displayName());
    } catch (UnsupportedEncodingException e) {
      logException(e);
    }
    return outStream.toString();
  }

  protected String foundInvalidRequestBody(Result result) {
    result.setIsFail(true).setDescription("Unable deserialize request body");
    return new Gson().toJson(result);
  }

  private void logException(Exception e) {
    Log.e("Service Error", e.getCause().toString());
  }

  private void writeErrorToOutStream(IOException e) {
    try {
      outStream.write(e.getCause().toString().getBytes(Charset.defaultCharset()));
    } catch (IOException e1) {
      logException(e);
    }
  }
}
