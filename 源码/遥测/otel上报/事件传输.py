'可取消的普通事件 HTTP 导出，含重试等待'
import gzip,time,threading
from requests import Session as 请求会话
from .传输 import 日志传输选项,记录体
from ...基础设施.通用工具.序列化编码 import 紧凑json编码

__all__=['创建事件日志导出器']

重试状态码=frozenset((429,502,503,504))
响应上限=4*1024*1024

def 创建事件日志导出器(选项,信号):
    '这一通道的导出器；取消会放开请求和重试，关闭时拆掉自己的连接'
    配置=日志传输选项(选项)
    会话=请求会话()
    锁=threading.Lock()
    关闭期约={'值':None}

    def 已取消():
        '通道取消信号'
        return getattr(信号,'aborted',False) or getattr(信号,'is_set',lambda:False)()

    def 导出(记录,回调):
        '发送一批；失败交给回调'
        try:
            if 已取消():
                raise RuntimeError('OTLP export cancelled')
            正文=紧凑json编码(记录体(记录,{**选项,'resourceAttributes':选项.get('resourceAttributes'),'scope':选项.get('scope')})).encode('utf-8')
            压缩=配置['compression']=='gzip'
            数据=gzip.compress(正文) if 压缩 else 正文
            头=配置['headers']()
            if 压缩:
                头={**头,'content-encoding':'gzip'}
            if 配置['userAgent'] is not None:
                头={**头,'user-agent':配置['userAgent']}
            等待=0.2
            最后错误=None
            for 次数 in range(6):
                if 已取消():
                    raise RuntimeError('OTLP export cancelled')
                响应=会话.post(
                    配置['url'],data=数据,headers=头,
                    timeout=配置['timeoutMillis']/1000.0,allow_redirects=False,
                )
                if len(响应.content)>响应上限:
                    raise RuntimeError('OTLP response exceeded 4 MiB')
                if 响应.status_code<300:
                    if 回调 is not None:
                        回调({'code':0})
                    return
                最后错误=RuntimeError('OTLP collector returned HTTP '+str(响应.status_code))
                if 响应.status_code not in 重试状态码 or 次数==5:
                    raise 最后错误
                time.sleep(min(等待,5))
                等待*=2
            raise 最后错误
        except Exception as 错误:
            if 回调 is not None:
                回调({'code':1,'error':错误})

    def 强制刷出():
        '没有额外队列'
        return None

    def 关闭():
        '只关一次，并拆掉连接'
        with 锁:
            if 关闭期约['值'] is not None:
                return 关闭期约['值']
            会话.close()
            关闭期约['值']=True
        return None

    return {'export':导出,'forceFlush':强制刷出,'shutdown':关闭}
