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

import android.content.Context;
import android.telephony.TelephonyManager;
import android.util.Log;
import com.android.devtools.server.model.RestServiceModel;
import com.android.devtools.server.model.Result;
import com.android.devtools.server.model.TelephonyManagerModel;
import com.google.gson.Gson;
import java.io.IOException;

/**
 * Service for phone(calling status) of phone.
 */
public class TelephonyManagerService implements Service {

  private static final String TAG = TelephonyManagerService.class.getSimpleName();
  private TelephonyManager telephonyManager = null;
  private Result result = new Result();

  public TelephonyManagerService(Context c) {
    telephonyManager = (TelephonyManager) c.getSystemService(Context.TELEPHONY_SERVICE);
  }

  @Override
  public String execute(String json) throws IOException {
    boolean isSuccess = false;

    TelephonyManagerModel telephonyModel = new Gson().fromJson(json, TelephonyManagerModel.class);
    if (telephonyModel == null) {
      Log.e(TAG, "TelephonyManagerModel null. Invalid POST Request body: " + json);
      result.setIsFail(true);
      result.setDescription("Invalid POST Request Body");
      return new Gson().toJson(result);
    }
    int callState = telephonyManager.getCallState();
    switch (callState) {
      case TelephonyManager.CALL_STATE_IDLE:
      case TelephonyManager.CALL_STATE_OFFHOOK:
      case TelephonyManager.CALL_STATE_RINGING:
        isSuccess = true;
        result.setDescription(Integer.toString(callState));
        break;
      default:
        Log.e(TAG, "Invalid Action specified in POST Request");
        isSuccess = false;
        result.setDescription("Unknown Action specified in request.");
    }
    result.setIsFail(!isSuccess);
    return new Gson().toJson(result);
  }

  @Override
  public String toString() {
    return new Gson()
        .toJson(
            new RestServiceModel(
                POST, "/TelephonyManagerService", new TelephonyManagerModel("String").toString()));
  }
}
