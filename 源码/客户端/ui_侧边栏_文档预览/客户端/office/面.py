from ..面 import 已中止

__all__=['office面']

def office面(读取,描述失败):
    """把 Office 读取绑到存储动作，不把 Remote 交给组件。"""
    def 工厂(_会话标识,动作):
        def 加载(标签标识,修订,文件,信号,已载,失败):
            if 已中止(信号):
                return
            动作['loading'](标签标识,修订)
            try:
                结果=读取(文件,信号)
                if hasattr(结果,'等待'):
                    结果=结果.等待()
            except Exception as 错误:
                if 已中止(信号):
                    return
                消息=错误.args[0] if len(错误.args)>0 else str(错误)
                动作['failed'](标签标识,修订,{'code':'gateway/internal','message':描述失败({'message':消息})})
                失败()
                return
            if 已中止(信号):
                return
            if isinstance(结果,dict) and 结果.get('ok') is True:
                动作['complete'](标签标识,修订,结果['value'])
                已载(结果['value']['version'])
            else:
                错=结果.get('error') if isinstance(结果,dict) else None
                码=错.get('code') if isinstance(错,dict) else 'gateway/internal'
                动作['failed'](标签标识,修订,{'code':码,'message':描述失败(错 if 错 is not None else {'message':str(结果)})})
                失败()
        return {'load':加载}
    return 工厂
