from .计划 import 解析计划地址,已提交计划#计划解析

__all__=['计划资源提供者']#仅中文公开名

def 造失败(码,消息,细节=None):
    """RemoteFailure 形 dict。"""
    return {'code':码,'message':消息,'details':细节 if 细节 is not None else {}}#失败

def 计划资源提供者(远程会话):
    """绑定计划读取到会话 Remote；找到精确调用后停。"""
    def 打开(地址,选项=None):
        """同步生成器：逐帧产出 RemoteResult。"""
        信号=选项['signal'] if 选项 is not None and 'signal' in 选项 else None#中止 Event
        def 已中止():
            """信号已中止。"""
            return 信号 is not None and 信号.is_set()#中止
        if 已中止():#已中止
            return#停
        目标=解析计划地址(地址)#解析
        if 目标 is None:#无效
            yield {'ok':False,'error':造失败('plan/invalid-address','Invalid plan resource address.')}#失败
            return#停
        会话地址=目标['session']#会话
        try:#读取
            快照=None#快照帧
            for 帧 in 远程会话.follow({'address':会话地址},信号):#跟随
                if 帧['type']=='snapshot':#快照
                    快照=帧#记下
                    break#停跟
            if 已中止():#已中止
                return#停
            if 快照 is None:#无快照
                yield {'ok':False,'error':造失败('plan/unavailable','Session history ended before the plan could be read.')}#不可用
                return#停
            页={'records':快照['records'],'hasMore':快照['hasMore']}#当前页
            while True:#翻页
                for 条目 in 页['records']:#逐条
                    计划=已提交计划(条目['event'])#解析
                    if 计划 is not None and 计划['callId']==目标['callId']:#命中
                        yield {'ok':True,'value':计划}#成功
                        return#停
                记录=页['records']#记录
                前序=记录[0]['event']['seq'] if len(记录)>0 else None#页首
                if not 页['hasMore'] or 前序 is None:#无更多
                    break#停
                下一=远程会话.page({'address':会话地址,'throughSeq':快照['cursor'],'beforeSeq':前序},信号)#翻页
                if 已中止():#已中止
                    return#停
                if not 下一['ok']:#失败
                    yield 下一#透传
                    return#停
                页=下一['value']#下一页
            yield {'ok':False,'error':造失败('plan/not-found','The submitted plan was not found in this Session.')}#未找到
        except Exception as 错误:#捕获
            if not 已中止():#未中止才报
                文=错误.args[0] if len(错误.args)>0 else str(错误)#文
                yield {'ok':False,'error':造失败('plan/read-failed',文 if isinstance(文,str) else str(文))}#失败帧
    return {'protocol':'plan','open':打开}#提供者
