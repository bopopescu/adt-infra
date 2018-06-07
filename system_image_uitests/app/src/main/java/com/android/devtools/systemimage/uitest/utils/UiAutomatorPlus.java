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

import android.app.Instrumentation;
import android.support.test.uiautomator.By;
import android.support.test.uiautomator.BySelector;
import android.support.test.uiautomator.UiDevice;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiObject2;
import android.support.test.uiautomator.UiObjectNotFoundException;
import android.support.test.uiautomator.UiSelector;

import java.util.ArrayList;
import java.util.List;

/**
 * UiAutomator additions to provide handy, high-level wrapper APIs.
 */
public class UiAutomatorPlus {

    private UiAutomatorPlus() {
        throw new AssertionError();
    }

    /**
     * Finds an object that is under the same cell of a container with a relative object.
     * @param instrumentation see {@link android.test.InstrumentationTestCase#getInstrumentation()
     *                        getInstrumentation}
     * @param target the {@link BySelector} of the target object
     * @param relative the {@link BySelector} of the relative object
     * @param container the {@link BySelector} of the container object,
     *                  e.g., ListView, ViewGroup, etc.
     * @return the target object
     * @throws UiObjectNotFoundException if it fails to find a UI object.
     */
    public static UiObject2 findObjectByRelative(Instrumentation instrumentation,
                                                 BySelector target,
                                                 BySelector relative,
                                                 BySelector container,
                                                 Integer... depth)
            throws UiObjectNotFoundException {
        UiDevice device = UiDevice.getInstance(instrumentation);
        List<UiObject2> containers = device.findObjects(container);
        List<UiObject2> matchedObjects = new ArrayList<>();
        for (UiObject2 object: containers) {
            for (UiObject2 cell: object.getChildren()) {
                if (depth.length==0) {
                    matchedObjects.addAll(
                            cell.findObjects(By.hasDescendant(target).hasDescendant(relative)));
                }
                else {
                    matchedObjects.addAll(
                            cell.findObjects(By.hasDescendant(
                                    target, depth[0]).hasDescendant(relative, depth[0])));
                }
            }
        }
        if (matchedObjects.size() == 0) {
            throw new UiObjectNotFoundException("Failed to find the target object.");
        } else if (matchedObjects.size() > 1){
            throw new AssertionError("Found more than one objects by relative");
        } else {
            return matchedObjects.get(0).findObject(target);
        }
    }

    /**
     * Find an object that matches any selector in a selector list.
     * @param instrumentation see {@link android.test.InstrumentationTestCase#getInstrumentation()
     *                        getInstrumentation}
     * @param selectors the list of candidate {@link BySelector}s
     * @return the target object
     * @throws UiObjectNotFoundException if it fails to find a UI object.
     */
    public static UiObject2 findObjectMatchingAny(Instrumentation instrumentation,
                                               BySelector... selectors)
            throws UiObjectNotFoundException {
        UiDevice device = UiDevice.getInstance(instrumentation);
        for (BySelector selector:selectors) {
            UiObject2 object = device.findObject(selector);
            if (object != null) {
                return object;
            }
        }
        throw new UiObjectNotFoundException("Failed to find the matching UI object.");
    }

    /**
     * Find an object that matches any selector in a selector list.
     * @param instrumentation see {@link android.test.InstrumentationTestCase#getInstrumentation()
     *                        getInstrumentation}
     * @param selectors the list of candidate {@link UiSelector}s
     * @return the target object
     * @throws UiObjectNotFoundException if it fails to find a UI object.
     */
    public static UiObject findObjectMatchingAny(Instrumentation instrumentation,
                                             UiSelector... selectors)
            throws UiObjectNotFoundException {
        UiDevice device = UiDevice.getInstance(instrumentation);
        for (UiSelector selector:selectors) {
            UiObject object = device.findObject(selector);
            if (object.exists()) {
                return object;
            }
        }
        throw new UiObjectNotFoundException("Failed to find the matching UI object.");
    }
}
