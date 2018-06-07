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
package com.android.devtools.systemimage.uitest.smoke;

import android.app.Instrumentation;
import android.support.test.runner.AndroidJUnit4;
import android.support.test.uiautomator.UiDevice;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiScrollable;
import android.support.test.uiautomator.UiSelector;
import android.widget.EditText;
import android.widget.ListView;
import android.widget.ScrollView;
import android.widget.TextView;

import com.android.devtools.systemimage.uitest.annotations.TestInfo;
import com.android.devtools.systemimage.uitest.common.Res;
import com.android.devtools.systemimage.uitest.framework.SystemImageTestFramework;
import com.android.devtools.systemimage.uitest.utils.AppLauncher;
import com.android.devtools.systemimage.uitest.utils.Wait;
import com.android.devtools.systemimage.uitest.watchers.MapsWatcher;

import org.junit.Assert;
import org.junit.Rule;
import org.junit.Test;
import org.junit.runner.RunWith;

import java.util.concurrent.TimeUnit;

import static org.junit.Assert.assertTrue;

/**
 * Sanity test for Maps App
 */

@RunWith(AndroidJUnit4.class)
public class MapsTest {
    private static final String QUERY_STRING = "San Francisco";

    @Rule
    public final SystemImageTestFramework testFramework = new SystemImageTestFramework();

    /**
     * Verify the functionality of navigation overview in Google Maps app.
     * <p>
     * This is run to qualify releases. Please involve the test team in substantial changes.
     * <p>
     * TT ID: 4578f63f-7d2e-4e5e-a4e0-0ce2ae67982e
     * <p>
     * <pre>
     *   Test Steps:
     *   1. Launch emulator avd.
     *   2. Open Maps app.
     *   3. Accept terms and condition.
     *   4. Tap on search bar.
     *   5. Enter search query, "San Francisco", select it from the auto fill results.
     *   6. "San Francisco" location card opens.
     *   7. Select "San Francisco".
     *   8. Tap on the Drive icon.
     *   Verify:
     *   1. Map points to San Francisco location.
     *   2. Navigation overview is displayed.
     *   </pre>
     */
    @Test
    @TestInfo(id = "4578f63f-7d2e-4e5e-a4e0-0ce2ae67982e")
    public void testMapsApp() throws Exception {
        Instrumentation instrumentation = testFramework.getInstrumentation();
        UiDevice mDevice = testFramework.getDevice();

        if (testFramework.isGoogleApiImage() || testFramework.isGoogleApiAndPlayImage()) {
            AppLauncher.launch(instrumentation, "Maps");

            new MapsWatcher(mDevice).checkForCondition();

            final UiObject searchUiObject = mDevice.findObject(new UiSelector().
                    resourceIdMatches(Res.SEARCH_TEXT_BOX));
            assertTrue("Failed to find search text box", new Wait(5L).until(new Wait.ExpectedCondition() {
                @Override
                public boolean isTrue() throws Exception {
                    return searchUiObject.exists();
                }
            }));

            searchUiObject.clickAndWaitForNewWindow();

            UiObject searchEditText;
            UiObject selectedLocation;
            searchEditText = searchUiObject.getChild(new UiSelector().className(EditText.class.getName()));
            searchEditText.setText(QUERY_STRING);
            UiScrollable scrollView = new UiScrollable(new UiSelector().className(ScrollView.class.getName()));
            scrollView.scrollIntoView(new UiSelector().text(QUERY_STRING));
            selectedLocation = scrollView.getChildByText(new UiSelector()
                    .className(TextView.class.getName()), QUERY_STRING);
            Assert.assertTrue(selectedLocation.exists());
            selectedLocation.clickAndWaitForNewWindow();

            // Verify the Query String is present after completing search.
            UiObject searchTextView =
                    searchUiObject.getChild(new UiSelector().className(TextView.class.getName()));
            Assert.assertTrue(searchTextView.getText().contains(QUERY_STRING));

            // Verify the directions/route link exists and clicking on it opens the directions page
            // verify query string is pre filled in the destination("to") field.
            UiObject directions;
            boolean isSuccess = mDevice.findObject(new UiSelector().descriptionMatches(".*Directions.*|.*Route.*"))
                    .waitForExists(TimeUnit.MILLISECONDS.convert(3L, TimeUnit.SECONDS));

            if (isSuccess) {
                directions = mDevice.findObject(new UiSelector().descriptionMatches(".*Directions.*|.*Route.*"));
            } else {
                directions = mDevice.findObject(new UiSelector().text("DIRECTIONS"));
            }
            Assert.assertTrue(directions.exists());
            directions.clickAndWaitForNewWindow();

            UiObject destination = mDevice.findObject(new UiSelector().textContains(QUERY_STRING));
            new MapsWatcher(mDevice).checkForCondition();

            Assert.assertTrue(destination.exists());

            for (int i = 0; i < 5; i++) {
                mDevice.pressBack();
            }
        }
    }
}