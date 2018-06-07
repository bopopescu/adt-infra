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

package com.android.devtools.systemimage.uitest.annotations;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface TestInfo {

    /**
     * This provides the root of the TestRail link that describes the test verbally.
     * Only specify the root link if it differs from the default one.
     * Test description links will be used for the bug report package automation
     * to help developers to reproduce a bug.
     */
    String rootLink() default "http://android-testrail.hot.corp.google.com/testrail/index.php?/cases/view/";

    /**
     * This provides the id of the test in the TestRail.
     * {@code rootLink} plus {@code id} should form a complete link to the test case description.
     */
    String id() default "";
}
