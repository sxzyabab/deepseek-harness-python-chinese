class 平台认证错误(Exception):
    '稳定码，不携带响应体或授权 URL'
    def __init__(自身,码):
        '码为 network/protocol/expired/storage'
        super().__init__('account: '+码)
        自身.code=码
