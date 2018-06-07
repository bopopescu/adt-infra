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

import com.google.common.base.Stopwatch;

import android.os.SystemClock;

import java.util.concurrent.TimeUnit;

/**
 * Generic wait class which allows tests to await expected conditions becoming true.
 * <p>
 * Expected use:
 * new wait(timeout, polltime).until(expectedCondition);
 */
public class Wait {
    private static final long DEFAULT_WAIT_TIME = TimeUnit.MILLISECONDS.convert(3L, TimeUnit
            .SECONDS);
    private static final long DEFAULT_POLL_TIME =
            TimeUnit.MILLISECONDS.convert(100L, TimeUnit.MILLISECONDS);

    private long timeout;
    private long polltime;

    public Wait() {
        this(DEFAULT_WAIT_TIME, DEFAULT_POLL_TIME);
    }

    public Wait(long timeout) {
        this(timeout, DEFAULT_POLL_TIME);
    }

    public Wait(long timeout, long polltime) {
        this.timeout = timeout;
        this.polltime = polltime;
    }

    /**
     * Polls the given expected condition at the given poll ratail either
     * the given ExpectedCondition's isTrue method returns true or timeout is
     * reached.
     *
     * @param expectedCondition the expected condition to meet
     * @return {@code true} if the given ExpectedCondition's isTrue method returns
     * true before timeout is reached, or {@code false} otherwise.
     */
    public boolean until(ExpectedCondition expectedCondition) throws Exception {
        Stopwatch stopwatch = Stopwatch.createStarted();
        while (stopwatch.elapsed(TimeUnit.MILLISECONDS) < timeout) {
            if (expectedCondition.isTrue()) {
                return true;
            }
            SystemClock.sleep(polltime);
        }
        return false;
    }

    public interface ExpectedCondition {
        /**
         * Interface method to check if the condition meets.
         *
         * @return true if waited on condition holds,
         * or false will cause wait to block and invoke again after the poll time.
         */
        boolean isTrue() throws Exception;
    }
}
