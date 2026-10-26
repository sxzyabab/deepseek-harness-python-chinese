'仓库文件：能匿名读的走单文件接口，其余走部分克隆'
import threading#等期约
from urllib.parse import quote,urlparse#编码与源站
from ...工具.插件详情 import (
    详情失败,#读失败
    编码路径,#路径段编码
    请求正文,#有界 HTTP
    自述文件名表,#精确文件名
    按名读自述,#按名找 README
)#详情文件

__all__=['仓库文件','等到结果']#仅中文公开名

def 等到结果(结果):
    '依赖若返回带 然后 的期约则阻塞到结算；普通值原样返回'
    然后=getattr(结果,'然后',None)#期约
    if not callable(然后):#已经是值
        return 结果#原样
    完成=threading.Event()#结算
    盒子={}#值或错误

    def 成功(结果值=None):
        '兑现'
        盒子['值']=结果值#记下
        完成.set()#放开

    def 失败(错误=None):
        '拒绝'
        if isinstance(错误,BaseException):#异常
            盒子['错误']=错误#原样
        elif 错误 is None:#没有原因
            盒子['错误']=Exception('rejected')#占位
        else:#其它原因
            盒子['错误']=Exception(str(错误))#收成异常
        完成.set()#放开

    然后(成功,失败)#挂上
    完成.wait()#阻塞
    if '错误' in 盒子:#被拒绝
        raise 盒子['错误']#交给调用方
    return 盒子.get('值')#兑现的值

def 接口网址(接口,仓库,引用,路径):
    'GitHub 原始文件或 GitLab 仓库文件 API'
    if 接口=='github':#原始主机
        return 'https://raw.githubusercontent.com/'+仓库['project']+'/'+quote(引用,safe='')+'/'+编码路径(路径)#GitHub
    源=urlparse(仓库['url']).scheme+'://'+urlparse(仓库['url']).netloc#保留自建 GitLab 的方案和端口
    项目=quote(仓库['project'],safe='')#项目
    文件=quote(路径,safe='')#文件
    return 源+'/api/v4/projects/'+项目+'/repository/files/'+文件+'/raw?ref='+quote(引用,safe='')#GitLab

def 仓库文件(仓库,提交,选项):
    '一份仓库在某提交上的文件。提交缺省为默认分支'
    if 仓库['host']=='github.com':#固定 GitHub
        接口='github'#原始文件
    elif 仓库['host'] in 选项['gitlab主机']:#配置的 GitLab
        接口='gitlab'#文件 API
    else:#没有匿名单文件接口
        接口=None#只走克隆
    引用=提交 if 提交 is not None else 'HEAD'#引用
    缓存=选项['缓存']#部分克隆

    def 从接口(路径,最大字节,信号,经由):
        '接口读到的字节。401、403、404 无法区分缺文件和私有仓库，返回 None'
        正文=等到结果(请求正文(接口网址(经由,仓库,引用,路径),最大字节,信号,{
            'timeoutMs':选项['超时毫秒'],#时限
            'lifetime':选项['寿命'],#寿命
        }))#请求
        if 正文.get('ok') is True:#成功
            return 正文.get('bytes')#字节
        状态=正文.get('status')#状态
        if 状态!=404 and 状态!=401 and 状态!=403:#其它状态
            raise 详情失败('network',仓库['url']+': '+路径+' answered HTTP '+str(状态))#网络
        return None#无法区分

    def 读取(路径,最大字节,信号):
        '读一个普通文件'
        if 接口 is not None:#有接口
            字节=从接口(路径,最大字节,信号,接口)#先问接口
            if 字节 is not None or 等到结果(缓存.是否公开(仓库['url'])):#公开仓库的缺失即不存在
                return 字节#字节或 None
        return 等到结果(缓存.读取(仓库['url'],提交,路径,最大字节,信号))#克隆

    def 读自述(目录,最大字节,信号):
        '读目录里的 README'
        if 接口 is not None:#有接口
            def 读一个(路径,上限,读信号):
                '接口读文件'
                return 从接口(路径,上限,读信号,接口)#字节或 None
            找到=等到结果(按名读自述(读一个,目录,最大字节,信号,自述文件名表[:1]))#先问最常见的名字
            if 找到 is not None:#有
                return 找到#文件
            if 等到结果(缓存.是否公开(仓库['url'])):#缺失可信
                return 等到结果(按名读自述(读一个,目录,最大字节,信号,自述文件名表[1:]))#其余名字
        return 等到结果(缓存.读自述(仓库['url'],提交,目录,最大字节,信号))#克隆

    return {'key':'git:'+仓库['url']+'#'+引用,'read':读取,'readme':读自述}#文件源
