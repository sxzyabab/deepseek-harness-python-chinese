class 平台认证错误(Exception):
    '稳定码，不携带响应体或授权 URL'
    def __init__(自身,码):
        '码为 no-response/network/protocol/expired/storage'
        super().__init__('account: '+码)
        自身.code=码

class 账号未授权错误(平台认证错误):
    '令牌被平台以 401 或业务码 40003 拒绝'
    def __init__(自身):
        '固定 expired'
        super().__init__('expired')
