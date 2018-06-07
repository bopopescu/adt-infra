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

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

public class ShellUtil {
    public static final String TAG = ShellUtil.class.getName();

    private ShellUtil() {
        throw new AssertionError();
    }

    /**
     * Invokes shell command.
     * <p>
     * Note shell commands that require system privilege cannot be invoked through the method.
     *
     * @param cmd the command to call in shell
     * @return {@link ShellResult}
     * @throws IOException if File IO fails.
     */
    public static ShellResult invokeCommand(String cmd) throws IOException {
        Process p = Runtime.getRuntime().exec(cmd);
        BufferedReader stdoutReader = new BufferedReader(new InputStreamReader(p.getInputStream()));
        BufferedReader stderrReader = new BufferedReader(new InputStreamReader(p.getErrorStream()));
        String line;
        StringBuilder stdout = new StringBuilder();
        while ((line = stdoutReader.readLine()) != null) {
            stdout.append(line).append("\n");
        }
        stdoutReader.close();
        StringBuilder stderr = new StringBuilder();
        while ((line = stderrReader.readLine()) != null) {
            stdout.append(line).append("\n");
        }
        stderrReader.close();
        if (p != null) {
            p.destroy();
        }
        return new ShellResult(stdout.toString(), stderr.toString());
    }

    /**
     * Shell result class definition.
     */
    public static class ShellResult {
        public final String stdout;
        public final String stderr;

        /**
         * Constructs the class.
         */
        public ShellResult(String stdout, String stderr) {
            this.stdout = stdout;
            this.stderr = stderr;
        }
    }
}
