package com.android.devtools.server.utils;

/**
 * Constants used among different services.
 */

public class Constants {
  public static final String APPS = "Apps";
  public static final String LAUNCHER_LIST_CONTAINER_RES =
      "(com.android.launcher\\d*:id|com.google.android."
      + "googlequicksearchbox\\d*:id|com.google.android.apps."
      + "nexuslauncher\\d*:id)/(all_apps_container|apps_customize_pane_content|apps_list_view)";
  public static final String TEXT_VIEW_CLASS_NAME = "android.widget.TextView";
  public static final String TIP_BUTTON_OK = "OK";
  public static final String TIP_BUTTON_GOT_IT = "GOT IT";
  public static final String YES = "YES";
}
