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

package com.android.devtools.systemimage.uitest.unittest.utils;

import com.android.devtools.systemimage.uitest.annotations.TestInfo;
import com.android.devtools.systemimage.uitest.utils.ShellUtil;

import org.junit.Assert;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.Timeout;
import org.junit.runner.RunWith;

import android.support.test.runner.AndroidJUnit4;

/**
 * Unit test on {@link ShellUtil}.
 */
@RunWith(AndroidJUnit4.class)
public class ShellUtilTest {
    @Rule
    public Timeout globalTimeout = Timeout.seconds(60);

    @Test
    @TestInfo()
    public void testShellUtil() throws Exception {
        ShellUtil.ShellResult result = ShellUtil.invokeCommand("ls");
        Assert.assertTrue(result.stderr, result.stdout.length() > 0 && result.stderr.length() == 0);
    }
}
