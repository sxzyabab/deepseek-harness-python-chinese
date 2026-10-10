class WebhookGithub配置错误(Exception):
    '路由与来源配置非法'

class WebhookHttp错误(Exception):
    '消息可原样回写、不含请求数据的 HTTP 拒绝'
    def __init__(自身,状态码,消息):
        '记下 HTTP 状态码与安全消息'
        super().__init__(消息)
        自身.status=状态码#HTTP 状态码
