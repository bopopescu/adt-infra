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

package com.android.devtools.systemimage.uitest.common;

/**
 * Common resource IDs used to identify UI widgets by UiAutomator.
 * <p>
 * They could be String or regex String.
 */
public class Res {
    // System and Google application resource IDs ("com.android.*" or "com.google.*")

    public static final String BROWSER_BOOKMARKS_LABEL_RES = "com.android.browser:id/label";
    public static final String BROWSER_SEARCH_ICON_RES = "com.android.browser:/id/progress";
    public static final String BROWSER_URL_TEXT_FIELD_RES = "com.android.browser:id/url";
    public static final String BROWSER_TAB_SWITCHER_RES = "com.android.browser:id/tab_switcher";
    public static final String BROWSER_CLOSE_TAB_RES = "com.android.browser:id/closetab";

    public static final String CHROME_TERMS_ACCEPT_BUTTON_RES = "com.android.chrome:id/terms_accept";
    public static final String CHROME_SEARCH_BOX_RES = "com.android.chrome:id/search_box_text";
    public static final String CHROME_URL_BAR_RES = "com.android.chrome:id/url_bar";
    public static final String CHROME_MENU_BUTTON_RES = "com.android.chrome:id/menu_button";
    public static final String CHROME_MENU_BADGE_RES = "com.android.chrome:id/menu_badge";
    public static final String CHROME_SIGNIN_PROMO_RES = "com.android.chrome:id/signin_promo_signin_button";
    public static final String CHROME_SIGNIN_PROMO_CLOSE_RES = "com.android.chrome:id/signin_promo_close_button";
    public static final String CHROME_MORE_BUTTON_RES = "com.android.chrome:id/more_button";
    public static final String CHROME_CLOSE_MENU_BUTTON_RES = "com.android.chrome:id/close_menu_id";
    public static final String CHROME_TITLE_RES = "com.android.chrome:id/title";
    public static final String CHROME_NO_THANKS_BUTTON_RES = "com.android.chrome\\d*:id" + "/(no_thanks_button|negative_button)";
    public static final String CHROME_PROGRESS_BAR_RES = "com.android.chrome:id/progress";

    public static final String ANDROID_LAUNCHER_WELCOME_CLING_RES =
            "com.android.launcher\\d*:id/cling_dismiss";
    public static final String ANDROID_WELCOME_CLING_RES =
            "(com.android.launcher\\d*:id|com.google.android.googlequicksearchbox\\d*:id)"
                    + "/cling_dismiss_longpress_info";
    public static final String LAUNCHER_LIST_CONTAINER_RES =
            "(com.android.launcher\\d*:id|com.google.android.googlequicksearchbox\\d*:id|com.google.android.apps.nexuslauncher\\d*:id|com.android.launcher3\\d*:id/active)"
                    + "/(all_apps_container|all_apps_handle|apps_customize_pane_content|apps_list_view|drag_indicator)";

    public static final String ANDROID_PHONE_RES = "com.android.phone";
    public static final String ABOUT_PHONE_LIST_CONTAINER_RES =
            "com.android.settings:id/container_material";
    public static final String APPS_LIST_CONTAINER_RES = "com.android.settings:id/list_container";
    public static final String APPS_TAB_CONTAINER_RES = "com.android.settings:id/pager";
    public static final String NETWORK_SWITCHES_RECYCLER_VIEW_RES =
            "com.android.settings:id/list"; // Added in API 24
    public static final String SETTINGS_ADVANCED_OPTION_RES = "com.android.settings:id/advanced";
    public static final String SETTINGS_LIST_CONTAINER_RES =
            "(com.android.settings|android):id/(dashboard|list|dashboard_container)";
    public static final String SETTINGS_RECYCLER_VIEW_RES =
            "com.android.settings:id/dashboard_container"; // Added in API 24

    public static final String CAMERA_FRAME_RES = "com.android.camera2:id/camera_app_root";
    public static final String CAMERA_SHUTTER_BUTTON_RES = "com.android.camera2:id/shutter_button";
    public static final String CAMERA_FILE_THUMBNAIL_RES = "com.android.camera2:id/rounded_thumbnail_view";
    public static final String CAMERA_FILE_DELETE_RES = "com.android.camera2:id/filmstrip_bottom_control_delete";
    public static final String LOCK_SCREEN_ICON_RES = "com.android.systemui:id/lock_icon";
    public static final String VPN_LOCK_ICON_RES = "com.android.systemui:id/vpn";;
    public static final String NOTIFICATION_BAR_EXPAND_RES = "com.android.systemui:id/expand_indicator";
    public static final String NOTIFICATION_BAR_HEADER_RES = "com.android.systemui:id/header";

    public static final String GOOGLE_PLAY_VENDING_RES = "com.android.vending";
    public static final String GOOGLE_PLAY_IDLE_RES = "com.android.vending:id/search_box_idle_text";
    public static final String GOOGLE_PLAY_ACTIVE_RES = "com.android.vending:id/search_box_active_text_view";
    public static final String GOOGLE_PLAY_INPUT_RES =
            "com.android.vending:id/search_box_text_input";
    public static final String GOOGLE_PLAY_LIST_TITLE_RES = "com.android.vending:id/li_title";
    public static final String GOOGLE_PLAY_FILTER_TOGGLE_RES = "com.android.vending:id/content_filter_on_off_toggle";

    public static final String DIALER_PHONE_RES = "(com.android.dialer\\d*:id|com.google.android.dialer\\d*:id)/floating_action_button";
    public static final String DIALER_PAD_RES = "(com.android.dialer\\d*:id|com.google.android.dialer\\d*:id)/dialpad_floating_action_button";
    public static final String DIALER_DIGITS_RES = "(com.android.dialer\\d*:id|com.google.android.dialer\\d*:id)/digits";

    public static final String NOW_SIGNIN_ACCEPT_BUTTON_RES =
            "com.google.android.googlequicksearchbox\\d*:id/accept_button";
    public static final String NOW_SIGNIN_DECLINE_BUTTON_RES =
            "com.google.android.googlequicksearchbox\\d*:id/decline_button";
    public static final String NOW_SIGNIN_SCREEN_RES =
            "com.google.android.googlequicksearchbox\\d*:id/header_title";
    public static final String GOOGLE_BACKUP_SWITCH_RES =
            "com.google.android.gms:id/suw_items_switch";
    public static final String SIGN_IN_CONSENT_RES = "com.google.android.gms:id/signinconsentNext";

    public static final String SEARCH_TEXT_BOX =
            "(com.google.android.apps.maps:id|com.google.android.apps.gmm:id)" +
                    "/(search_omnibox_text_box|textbox|edit_textbox)";
    public static final String GOOGLE_AR_SNACKBAR_RES =
            "com.google.ar.core.examples.c.helloar:id/snackbar_text";

    // Third-party application resource IDs
    public static final String APP_IMAGE_VIEW_ID =
            "com.example.android.rs.hellocompute:id/displayin";
    public static final String START_VPN_BUTTON_RES = "com.test.vpn:id/start_vpn";

    // Platform resource IDs ("android.*")
    public static final String ANDROID_DATE_PICKER_HEADER_RES = "android:id/date_picker_header";
    public static final String ANDROID_DATE_PICKER_HEADER_RES_19 = "android:id/datePicker";
    public static final String ANDROID_TIME_HEADER_RES = "android:id/time_header";
    public static final String ANDROID_TIME_HEADER_RES_19 = "android:id/timePicker";
    public static final String ANDROID_LIST_RES = "android:id/list";
    public static final String ANDROID_CONTENT_RES = "android:id/content";
    public static final String ANDROID_TITLE_RES = "android:id/title";
}
