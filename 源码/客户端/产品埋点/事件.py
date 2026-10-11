'桌面埋点事件名与选定字段'

__all__=['引导页','产品事件字段','可选产品事件字段']

引导页=('onboarding_welcome','onboarding_recharge','onboarding_use_case','onboarding_process')

产品事件字段={
    'desktop_app_launch':(),
    'auth_page_view':(),
    'auth_page_click':('button_name',),
    'api_key_save_click':(),
    'onboarding_page_view':('page_name',),
    'onboarding_page_click':('page_name','button_name'),
    'onboarding_popup_view':('popup_name',),
    'onboarding_popup_click':('popup_name','button_name'),
    'desktop_upgrade_click':(),
    'desktop_upgrade_download_result':('is_success',),
    'desktop_upgrade_install_restart_click':(),
    'send_button_click':('run_mode','msg_type'),
    'model_switch':('switch_from','switch_to'),
    'thinking_level_switch':('switch_from','switch_to','model_name'),
    'context_compression':('session_id','trigger_type'),
    'branch_session_click':('session_id','parent_session_id','click_position'),
    'sidebar_menu_click':('menu_name',),
    'plugin_toggle':('plugin_name','plugin_type','is_enabled','is_builtin'),
    'plugin_add_button_click':(),
    'plugin_install_click':('input_value',),
    'install_plugin_result':('input_value','is_success','duration'),
    'confirm_uninstall_plugin':('plugin_name',),
}

可选产品事件字段={
    'onboarding_page_click':('selected_content',),
    'desktop_upgrade_download_result':('error_reason',),
    'send_button_click':('session_id','model_name','thinking_effort'),
    'model_switch':('session_id',),
    'thinking_level_switch':('session_id',),
    'branch_session_click':('parent_message_id',),
    'install_plugin_result':('error_reason','plugin_name'),
}
