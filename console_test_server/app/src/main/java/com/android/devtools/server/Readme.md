# Description:
   Android instrumentation test application that launches servlet on Android emulator.
   Set up console tests (e.g. GSM call test) via REST service.
## HOWTO:
  ./gradlew assemble ("gradle.bat assemble" for windows)
  adb install -r app/build/outputs/apk/app-debug.apk
  ./gradlew assembleAndroidTest ("gradle.bat" assembleAndroidTest for windows)
  adb install -r app/build/outputs/apk/app-debug-androidTest-unaligned.apk
  adb shell am instrument -w -e class com.android.devtools.server.Server com.android.devtools.server.test/android.support.test.runner.AndroidJUnitRunner
  adb -s emulator-5554 -e forward tcp:8080 tcp:8081
