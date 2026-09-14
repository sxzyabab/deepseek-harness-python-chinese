__all__=['请求主题列表']#仅中文公开名

请求主题列表=(#fetch主题列表
    'fetch/start','fetch/request-body-chunk','fetch/request-body-end',#请求侧
    'fetch/response','fetch/response-body-chunk','fetch/end','fetch/error',#响应侧
)#冻结字面量
