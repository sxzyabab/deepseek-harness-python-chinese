'条目详细介绍：包文档、仓库 README，以及读过的文档旁的图片'
import json,hashlib,posixpath,re,time,threading#清单、文档标识、目录、托管网址、并发读
from urllib.parse import urlparse#通用网址
from ...工具.标识构造 import 标识构造#文档标识，运行时原样返回
from ...工具.插件详情 import 详情失败,详情图片,拼接路径,取markdown,读包文档#文档选择
from .详情文件 import 仓库文件,等到结果#仓库文件与期约

__all__=['仓库于','清单仓库','详情读取器']#仅中文公开名

已知托管={#简写与站点到域
    'github':'github.com','gitlab':'gitlab.com','bitbucket':'bitbucket.org','gist':'gist.github.com',
}#已知托管结束
页面段=set(['tree','blob','commit','commits','raw','releases','issues','pull','wiki','src','browse'])#仓库页后缀，不属于项目路径

def 去掉片段(网址):
    '片段指修订，不属于仓库'
    return re.sub(r'#.*$','',网址)#去掉

def 路径段(路径):
    '去掉空段和尾部 .git'
    段表=[段 for 段 in 路径.split('/') if 段!='']#非空
    if len(段表)>0 and 段表[-1].endswith('.git'):#尾段
        段表[-1]=段表[-1][:-4]#去掉 .git
        if 段表[-1]=='':#只剩 .git
            段表.pop()#丢掉
    return 段表#段

def 托管信息(地址):
    'github、gitlab、bitbucket、gist 的拥有者与项目。gist 只标记种类'
    简写=re.match(r'^(github|gitlab|bitbucket|gist):(.+)$',地址,re.IGNORECASE)#简写
    if 简写 is not None:#简写
        种类=简写.group(1).lower()#种类
        if 种类=='gist':#代码片段
            return {'type':'gist'}#不是仓库
        段表=路径段(简写.group(2))#路径
        if len(段表)<2:#不够
            return None#不是
        项目=段表[1] if 种类!='gitlab' else '/'.join(段表[1:])#gitlab 允许子组
        return {'type':种类,'domain':已知托管[种类],'user':段表[0],'project':项目}#托管
    远程=re.match(r'^git@([^:]+):(.+)$',地址)#scp
    if 远程 is not None:#git@
        主机=远程.group(1).lower()#主机
        if 主机.startswith('www.'):#去掉 www
            主机=主机[4:]#裸主机
        段表=路径段(远程.group(2))#路径
    else:#网址
        去掉协议=re.sub(r'^git\+','',地址)#git+https
        if '://' not in 去掉协议:#不是网址
            return None#交给通用解析
        解析=urlparse(去掉协议)#拆开
        主机=解析.hostname.lower() if isinstance(解析.hostname,str) else ''#主机
        if 主机.startswith('www.'):#去掉 www
            主机=主机[4:]#裸主机
        段表=路径段(解析.path)#路径
    if 主机 in ('gist.github.com',):#代码片段站
        return {'type':'gist'}#不是仓库
    if 主机 not in ('github.com','gitlab.com','bitbucket.org'):#不是已知站
        return None#通用解析
    if '/-/' in 地址 and 主机=='gitlab.com':#GitLab 页面后缀交给通用解析剥掉
        return None#通用
    if len(段表)<2:#不够
        return None#不是
    if 主机=='gitlab.com':#子组算进项目
        项目='/'.join(段表[1:])#其余
    else:#拥有者/项目，丢掉 tree、blob 等页
        if len(段表)>2 and 段表[2] in 页面段:#页面
            段表=段表[:2]#只留仓库
        else:#两段
            段表=段表[:2]#仓库
        项目=段表[1]#项目
    种类={'github.com':'github','gitlab.com':'gitlab','bitbucket.org':'bitbucket'}[主机]#种类
    return {'type':种类,'domain':主机,'user':段表[0],'project':项目}#托管

def 仓库于(网址):
    '网址或简写指向的仓库。gist、其它协议、路径不足两段则没有'
    声明=去掉片段(网址)#去掉修订
    托管=托管信息(声明)#已知托管
    if 托管 is not None:#识别了
        if 托管.get('type')=='gist':#代码片段
            return None#不读
        项目=托管['user']+'/'+托管['project']#拥有者/项目
        return {'host':托管['domain'].lower(),'project':项目,'url':'https://'+托管['domain']+'/'+项目+'.git'}#https
    地址=re.sub(r'^git\+','',声明)#去掉 git+
    解析=urlparse(地址)#拆开
    if 解析.scheme=='' or 解析.netloc=='':#不是绝对网址
        return None#没有
    项目路径=re.sub(r'/-/.*$','',解析.path)#去掉 GitLab 页面
    项目路径=项目路径.strip('/')#两端斜杠
    项目路径=re.sub(r'\.git$','',项目路径)#去掉 .git
    if 解析.scheme not in ('https','http'):#方案
        return None#没有
    if 解析.username not in (None,'') or 解析.password not in (None,''):#凭据
        return None#没有
    if len([段 for 段 in 项目路径.split('/') if 段!=''])<2:#不足两段
        return None#没有
    return {'host':解析.hostname.lower(),'project':项目路径,'url':解析.scheme+'://'+解析.netloc+'/'+项目路径+'.git'}#仓库

def 规范化目录(目录):
    '用 / 分隔、没有空段和 .、.. 的目录。走出根则没有'
    规范=posixpath.normalize(目录.replace('\\','/')).rstrip('/')#规范
    if 规范 in ('.',''):#根
        return ''#根
    if 规范=='..' or 规范.startswith('../') or posixpath.isabs(规范):#离开仓库
        return None#丢掉
    return 规范#目录

def 清单仓库(值):
    '清单 repository 收成仓库与目录。directory 走出仓库则当成根'
    if isinstance(值,dict):#对象
        声明=值.get('url')#网址
        目录值=值.get('directory')#目录
    else:#字符串
        声明=值#自身
        目录值=None#无
    if not isinstance(声明,str):#不是字符串
        return None#没有
    仓库=仓库于(声明)#仓库
    if 仓库 is None:#不接受
        return None#没有
    目录=''#默认根
    if isinstance(目录值,str):#有目录
        规范=规范化目录(目录值)#规范
        目录='' if 规范 is None else 规范#走出根则丢掉
    仓库['directory']=目录#写入
    return 仓库#位置

持久失败=set(['too-large','denied','invalid'])#ttl 内再读仍会失败

class 详情读取器:
    '为一个服务缓存详细介绍和它旁边的图片'
    def __init__(自身,限度,仓库选项):
        '记下大小、寿命和仓库读取选项'
        自身.限度=限度#文档与图片上限、寿命
        自身.仓库选项=仓库选项#接口与克隆
        自身.结果表={}#键到缓存
        自身.进行中={}#键到进行中的读取
        自身.文档表={}#文档标识到文件源
        自身.表锁=threading.Lock()#结果与进行中

    def 读取(自身,位置,语言表,刷新=False):
        '并发读共用一次。结果和会重复的失败缓存 ttl'
        仓库=位置.get('repository')#仓库
        if isinstance(仓库,str):#manifest 哨兵
            仓库键=仓库#字面
        elif 仓库 is None:#没有
            仓库键=''#空
        else:#位置
            仓库键=仓库['url']+':'+仓库['directory']#网址加目录
        文件源=位置.get('files')#包文件
        文件键='' if 文件源 is None else 文件源.get('key') or ''#内容身份
        缓存键=json.dumps([文件键,位置.get('dir') or '',仓库键,list(语言表)],ensure_ascii=False,separators=(',',':'))#缓存键
        现在=现在毫秒()#现在
        缓存=自身.结果表.get(缓存键)#已有
        if not 刷新 and 缓存 is not None and 缓存['expiresAt']>现在:#未过期
            if 'failure' in 缓存:#会重复的失败
                raise 缓存['failure']#再抛
            if 缓存['value'].get('status')=='found':#找到过
                自身.使用(缓存['value']['document'])#续命
            return 缓存['value']#结果
        with 自身.表锁:#共用一次
            进行=自身.进行中.get(缓存键)#已有
            if 进行 is None:#本调用负责
                进行={'事件':threading.Event(),'盒子':{}}#盒子
                自身.进行中[缓存键]=进行#登记
                负责=True#负责
            else:#等待
                负责=False#不负责
        if not 负责:#等那一次
            进行['事件'].wait()#阻塞
            if '错误' in 进行['盒子']:#失败
                raise 进行['盒子']['错误']#再抛
            return 进行['盒子']['值']#结果
        try:#读取
            读到=自身.解析(位置,语言表,自身.仓库选项['寿命'])#选文档
            自身.记住(缓存键,{'value':读到,'expiresAt':现在毫秒()+自身.限度['ttl毫秒']})#缓存
            进行['盒子']['值']=读到#交给等待者
            return 读到#结果
        except Exception as 错误:#失败
            if isinstance(错误,详情失败) and 错误.reason in 持久失败:#再读仍失败
                自身.记住(缓存键,{'failure':错误,'expiresAt':现在毫秒()+自身.限度['ttl毫秒']})#记下
            进行['盒子']['错误']=错误#交给等待者
            raise#再抛
        finally:#摘掉
            进行['事件'].set()#放开
            with 自身.表锁:#摘
                if 自身.进行中.get(缓存键) is 进行:#仍是这一次
                    del 自身.进行中[缓存键]#摘掉

    def 图片(自身,标识,书写路径):
        '读文档旁的一张图片。浏览器放弃请求也不会中断共享克隆'
        文档=自身.使用(标识构造(标识))#续命并取出
        图片=None if 文档 is None else 详情图片(文档['path'],书写路径)#解析目标
        if 文档 is None or 图片 is None:#未知文档或路径不合法
            return None#没有
        字节=等到结果(文档['files']['read'](图片['path'],自身.限度['图片上限'],自身.仓库选项['寿命']))#读完
        if 字节 is None:#文件不存在
            return None#没有
        return {'bytes':字节,'mediaType':图片['mediaType']}#图片

    def 使用(自身,标识):
        '标记文档被用过，并忘掉超过 ttl 没人用的标识'
        现在=现在毫秒()#现在
        for 已知,文档 in list(自身.文档表.items()):#逐个
            if 现在-文档['usedAt']>自身.限度['ttl毫秒']:#过期
                del 自身.文档表[已知]#忘掉
        文档=自身.文档表.get(标识)#这一份
        if 文档 is not None:#还在
            文档['usedAt']=现在#续命
        return 文档#可能没有

    def 记住(自身,键,读取):
        '缓存一次读取，并丢掉已过期的'
        现在=现在毫秒()#现在
        for 已有键,已有 in list(自身.结果表.items()):#逐个
            if 已有['expiresAt']<=现在:#过期
                del 自身.结果表[已有键]#丢掉
        自身.结果表[键]=读取#写入

    def 解析(自身,位置,语言表,信号):
        '先包文档，再仓库 README'
        文件源=位置.get('files')#包文件
        目录=位置.get('dir') or ''#包目录
        仓库=None if 位置.get('repository')=='manifest' else 位置.get('repository')#仓库
        if 文件源 is not None:#能读包文件
            文档=等到结果(读包文档(文件源,目录,语言表,自身.限度['文档上限'],信号))#locale 或 README
            if 文档 is not None:#有
                return 自身.找到(文档['origin'],文件源,文档['path'],文档['markdown'])#文档
            if 位置.get('repository')=='manifest':#从清单找仓库
                仓库=自身.清单仓库于(文件源,目录,信号)#可能没有
        if 仓库 is None:#没有后续来源
            return {'status':'none'}#没有
        来源=仓库文件(仓库,None,自身.仓库选项)#默认分支
        自述=等到结果(来源['readme'](仓库['directory'],自身.限度['文档上限'],信号))#README
        if 自述 is None:#没有
            return {'status':'none'}#没有
        return 自身.找到('repository',来源,自述['path'],取markdown(自述['bytes']))#仓库文档

    def 清单仓库于(自身,文件源,目录,信号):
        '从包的 package.json 读 repository。读不懂则没有仓库'
        字节=等到结果(文件源['read'](拼接路径(目录,'package.json'),自身.限度['文档上限'],信号))#清单
        if 字节 is None:#没有清单
            return None#没有
        try:#解析
            清单=json.loads(字节.decode('utf-8'))#对象
        except (UnicodeDecodeError,json.JSONDecodeError):#不可读
            return None#不指向仓库
        if not isinstance(清单,dict):#不是对象
            return None#没有
        return 清单仓库(清单.get('repository'))#位置

    def 找到(自身,来源,文件源,路径,markdown):
        '登记文档标识。标识在 ttl 内被读到或被图片引用就继续有效'
        摘要=hashlib.sha256((str(文件源.get('key') or '')+'\0'+路径).encode('utf-8')).hexdigest()[:32]#内容摘要
        标识=标识构造(摘要)#文档标识
        自身.文档表[标识]={'files':文件源,'path':路径,'usedAt':现在毫秒()}#登记
        自身.使用(标识)#续命并清过期
        return {'status':'found','origin':来源,'markdown':markdown,'document':标识}#文档

def 现在毫秒():
    'Unix 毫秒'
    return int(time.time()*1000)#毫秒
