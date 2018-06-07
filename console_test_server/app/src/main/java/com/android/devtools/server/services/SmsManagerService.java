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
import com.android.devtools.server.model.RestServiceModel;
import com.android.devtools.server.model.SmsManagerModel;
import com.google.gson.Gson;

import java.io.IOException;

import android.content.Context;
import android.content.ContentResolver;
import android.database.Cursor;
import android.net.Uri;
import android.util.Log;

/**
 * Service for reading sms.
 */
public class SmsManagerService implements Service {

  private static final String TAG = SmsManagerService.class.getSimpleName();
  private static final String SMS_INBOX_URI = "content://sms/inbox";
  private static final String SMS_ADDRESS_COLUMN = "address";
  private static final String SMS_BODY_COLUMN = "body";
  private static final String SMS_SERVICE_PATH = "/SmsManagerService";
  private static final String ACTION = "String";
  private final Context mContext;

  public SmsManagerService(Context context) {
    mContext = context;
  }

  @Override
  public String execute(String json) throws IOException {
    boolean isSuccess = false;
    Result result = new Result();

    SmsManagerModel smsModel = new Gson().fromJson(json, SmsManagerModel.class);
    if (smsModel == null) {
      Log.e(TAG, "SmsManagerModel is null. Invalid POST Request body: " + json);
      result.setIsFail(true);
      result.setDescription("Invalid POST Request Body");
      return new Gson().toJson(result);
    }

    Uri smsQueryUri = Uri.parse(SMS_INBOX_URI);
    ContentResolver contentResolver = mContext.getContentResolver();
    Cursor cursor = null;

    try {
      cursor = contentResolver.query(smsQueryUri, null, null, null, null);

      if (cursor == null) {
        final String CURSOR_IS_NULL = "cursor is null.";
        Log.i(TAG, CURSOR_IS_NULL + " uri: " + smsQueryUri);
        result.setIsFail(!isSuccess);
        return new Gson().toJson(CURSOR_IS_NULL + " uri: " + smsQueryUri);
      }

      if(cursor.moveToFirst()) {
        for(String s : cursor.getColumnNames()){
          Log.d(TAG + "smsColumns", "Column: " + s);
        }

        final String address = cursor.getString(
                cursor.getColumnIndexOrThrow(SMS_ADDRESS_COLUMN));
        result.setSmsAddress(address);
        final String body = cursor.getString(
                cursor.getColumnIndexOrThrow(SMS_BODY_COLUMN));
        result.setSmsTextMessage(body);

        isSuccess = true;
      }
    } catch (NullPointerException npe) {
      Log.e(TAG, npe.getMessage());
      isSuccess = false;
      result.setDescription(Log.getStackTraceString(npe));
    } catch (Exception e) {
      Log.e(TAG, e.getMessage());
      isSuccess = false;
      result.setDescription(Log.getStackTraceString(e));
    } finally {
      cursor.close();
    }

    result.setIsFail(!isSuccess);
    return new Gson().toJson(result);
  }

  @Override
  public String toString() {
    return new Gson()
            .toJson(
                    new RestServiceModel(
                            POST,
                            SMS_SERVICE_PATH,
                            new SmsManagerModel(ACTION).toString()));
  }
}
