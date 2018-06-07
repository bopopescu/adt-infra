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

package com.android.devtools.server.model;

/**
 * Json model for HTTP response.
 */
public class Result {
  private boolean isFail;
  private String description;
  private String requestBody;
  private String windowHierarchy;
  private String smsAddress;
  private String smsTextMessage;
  private String screenOrientation;
  private String screenRotation;
  private String longitude;
  private String latitude;
  private String altitude;

  public boolean isFail() {
    return isFail;
  }

  public Result setIsFail(boolean isFail) {
    this.isFail = isFail;
    return this;
  }

  public String getDescription() {
    return description;
  }

  public Result setDescription(String description) {
    this.description = description;
    return this;
  }

  public String getRequestBody() {
    return requestBody;
  }

  public Result setRequestBody(String requestBody) {
    this.requestBody = requestBody;
    return this;
  }

  public String getWindowHierarchy() {
    return windowHierarchy;
  }

  public Result setWindowHierarchy(String windowHierarchy) {
    this.windowHierarchy = windowHierarchy;
    return this;
  }

  public String getSmsAddress() {
    return smsAddress;
  }

  public Result setSmsAddress(String smsAddress) {
    this.smsAddress = smsAddress;
    return this;
  }

  public String getSmsTextMessage() {
    return smsTextMessage;
  }

  public Result setSmsTextMessage(String smsTextMessage) {
    this.smsTextMessage = smsTextMessage;
    return this;
  }

  public String getScreenOrientation() {
    return screenOrientation;
  }

  public Result setScreenOrientation(String screenOrientation) {
    this.screenOrientation = screenOrientation;
    return this;
  }

  public String getScreenRotation() {
    return screenRotation;
  }

  public Result setScreenRotation(String screenRotation) {
    this.screenRotation = screenRotation;
    return this;
  }

  public String getLongitude() {
    return longitude;
  }

  public Result setLongitude(String longitude) {
    this.longitude = longitude;
    return this;
  }

  public String getLatitude() {
    return latitude;
  }

  public Result setLatitude(String latitude) {
    this.latitude = latitude;
    return this;
  }

  public String getAltitude() {
    return altitude;
  }

  public Result setAltitude(String altitude) {
    this.altitude = altitude;
    return this;
  }
}
