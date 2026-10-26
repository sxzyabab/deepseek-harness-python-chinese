'发现页的索引源、查询结果和详情读取'
import json
import re
import threading
from urllib.parse import quote,urljoin
from ....启动.插件装载.注册表 import npmmirror注册表
from ....客户端.存储 import 创建快照存储
from .呈现 import 已声明查询,初始查询

__all__=['页大小','详情键','发现控制']

页大小=50
最大页=100
详情文件路由='api/plugin-market/detail-file'
绝对目的=re.compile(r'^(?:[a-z][a-z\d+.-]*:|//|#)',re.IGNORECASE)
初始状态={
    'status':'idle','indexes':[],'selected':None,'listing':None,
    'editing':False,'draft':'','saving':False,'sourceFailure':None,
}

def 等远程(值):
    '期约结算后再往下走。普通值原样返回'
    if 值 is None:
        return None
    然后=None
    if hasattr(值,'然后'):
        然后=值.然后
    elif hasattr(值,'then'):
        然后=值.then
    if 然后 is None:
        return 值
    盒={'值':None,'错误':None,'完成':threading.Event()}
    def 成功(数据=None):
        '记下兑现'
        盒['值']=数据
        盒['完成'].set()
    def 失败(错误=None):
        '记下拒绝'
        盒['错误']=错误
        盒['完成'].set()
    然后(成功,失败)
    盒['完成'].wait()
    if 盒['错误'] is not None:
        raise 盒['错误']
    return 盒['值']

def 详情键(请求,语言):
    '语言、索引、包名、版本和是否 npm，合成这一次读取的键'
    体={'url':请求['url'],'name':请求['name'],'version':请求['version'],'npm':请求.get('npm') is True}
    return json.dumps([语言,体],ensure_ascii=False,separators=(',',':'))

def 列表失败种类(失败):
    '索引无效，或读取失败'
    if isinstance(失败,dict) and 失败.get('code')=='plugin-market/invalid-index':
        return 'invalid'
    return 'fetch'

def 源失败种类(失败):
    '地址无效、重复、当前环境不能保存，或其他原因'
    if not isinstance(失败,dict):
        return {'kind':'other','reason':''}
    码=失败.get('code')
    if 码=='plugin-market/invalid-index-url':
        细节=失败.get('details') or {}
        if 细节.get('reason')=='duplicate':
            return {'kind':'duplicate'}
        return {'kind':'invalid'}
    if 码=='plugin-market/settings-unavailable':
        return {'kind':'unavailable'}
    return {'kind':'other','reason':失败.get('message') or ''}

def 详情失败种类(失败):
    'Host 点名的详情失败原因。其余算 other'
    if isinstance(失败,dict) and 失败.get('code')=='plugin-market/detail-unavailable':
        细节=失败.get('details') or {}
        原因=细节.get('reason')
        if 原因 in ('too-large','network','denied','git-unavailable','invalid'):
            return 原因
    return 'other'

class 发现控制:
    '一个客户端上的索引读取和索引源编辑'
    def __init__(自身,上下文,取基址):
        '记下远程和页面基址。卸载后不再发布迟到的结果'
        自身.上下文=上下文
        自身.取基址=取基址
        自身.存储=创建快照存储(dict(初始状态))
        自身.详情=创建快照存储({})
        自身.已拆除=False
        自身.锁=threading.Lock()
        自身.详情读={}
        自身.详情序号=0
        自身.索引读=0
        自身.列表读=0
        自身.选择已添加=False
        def 空失败():
            '还没有失败的读取'
            return None
        自身.失败=空失败

    def 拆除(自身):
        '停止发布'
        自身.已拆除=True

    def 状态(自身):
        '当前发现快照'
        return 自身.存储.getSnapshot()

    def 打补丁(自身,部分):
        '在锁里合并下一态'
        with 自身.锁:
            当前=dict(自身.存储.getSnapshot())
            当前.update(部分)
            自身.存储.set(当前)

    def 起线程(自身,函数,*位置参数):
        '远程读取不占界面线程'
        线=threading.Thread(target=函数,args=位置参数)
        线.daemon=True
        线.start()

    def 询问(自身,请求):
        '远程结果保持 ok/value。抛出的错误收成失败应答'
        try:
            应答=等远程(请求())
        except Exception as 错误:
            return {'ok':False,'error':{'code':'','message':str(错误),'details':{}}}
        if isinstance(应答,dict) and 'ok' in 应答:
            return 应答
        return {'ok':True,'value':应答}

    def 面(自身,解析文本):
        '标签页拿到的状态源和动作'
        详情=自身.详情面()
        钩子=dict(详情['hooks'])
        钩子['discover']=自身.存储
        return {
            'hooks':钩子,
            'loadDetail':详情['loadDetail'],
            'retryDetail':详情['retryDetail'],
            'detailImage':详情['detailImage'],
            'resolveText':解析文本,
            'ensure':自身.确保,
            'reload':自身.重载,
            'select':自身.选择,
            'search':自身.搜索,
            'more':自身.更多,
            'refresh':自身.刷新,
            'retry':自身.重试,
            'toggleSources':自身.切换源,
            'editDraft':自身.编辑草稿,
            'addSource':自身.添加源,
            'removeSource':自身.移除源,
        }

    def 详情面(自身):
        '详情区和图片地址'
        return {
            'hooks':{'details':自身.详情,'locale':自身.上下文.locale},
            'loadDetail':自身.加载详情,
            'retryDetail':自身.重试详情,
            'detailImage':自身.详情图,
        }

    def 确保(自身):
        '第一次画到才读索引源'
        if 自身.状态()['status']=='idle':
            自身.起线程(自身.读索引)

    def 重载(自身):
        '失败后再读索引源'
        自身.起线程(自身.读索引)

    def 选择(自身,网址):
        '换一个索引，并从初始查询读第一页'
        if 自身.状态().get('selected')==网址:
            return
        自身.打补丁({'selected':网址})
        自身.起线程(自身.加载,网址,初始查询,页大小,False)

    def 搜索(自身,查询):
        '替换当前索引的查询并读第一页'
        列表=自身.状态().get('listing')
        if 列表 is not None:
            自身.起线程(自身.加载,列表['url'],查询,页大小,False)

    def 更多(自身):
        '再读一页'
        自身.起线程(自身.加载更多)

    def 重试(自身):
        '再跑上一次失败的读取'
        自身.起线程(自身.失败)

    def 刷新(自身):
        '让 Host 重新取当前索引'
        列表=自身.状态().get('listing')
        if 列表 is not None:
            自身.起线程(自身.加载,列表['url'],列表['query'],页大小,True)

    def 切换源(自身):
        '打开或关上索引源编辑，并清掉上一次保存失败'
        状态=自身.状态()
        自身.打补丁({'editing':状态.get('editing') is not True,'sourceFailure':None})

    def 编辑草稿(自身,文本):
        '改草稿并清掉保存失败'
        自身.打补丁({'draft':文本,'sourceFailure':None})

    def 添加源(自身):
        '空白草稿不提交。新源成为选中索引'
        草稿=自身.状态().get('draft') or ''
        草稿=草稿.strip()
        if 草稿=='':
            return
        with 自身.锁:
            自身.选择已添加=True
        网址列=[索引['url'] for 索引 in 自身.状态().get('indexes') or []]
        网址列.append(草稿)
        自身.起线程(自身.保存源,网址列,True)

    def 移除源(自身,网址):
        '从列表里去掉这个索引源'
        网址列=[]
        for 索引 in 自身.状态().get('indexes') or []:
            if 索引['url']!=网址:
                网址列.append(索引['url'])
        自身.起线程(自身.保存源,网址列,False)

    def 加载详情(自身,请求,语言):
        '这一键还没有结果才读'
        键=详情键(请求,语言)
        if 键 not in 自身.详情.getSnapshot():
            自身.起线程(自身.读详情,请求,语言,False)

    def 重试详情(自身,请求,语言):
        '要求 Host 重新读，不拿缓存'
        自身.起线程(自身.读详情,请求,语言,True)

    def 详情图(自身,文档,目的):
        '绝对地址、协议相对地址和片段不改写。其余走 Host 的详情文件路由'
        if 绝对目的.match(目的):
            return None
        查询='document='+quote(str(文档),safe='')+'&path='+quote(目的,safe='')
        return urljoin(自身.取基址(),详情文件路由+'?'+查询)

    def 详情重置(自身):
        '连接重置后丢掉全部详情。图片用的文档标识已经失效'
        自身.详情读.clear()
        自身.详情.set({})

    def 源变更(自身):
        '还没画过则保持空闲'
        if 自身.状态()['status']!='idle':
            自身.起线程(自身.读索引)

    def 组合包变更(自身):
        '已就绪的列表按已加载条数重读，刷新安装状态'
        列表=自身.状态().get('listing')
        if 列表 is None or 列表.get('status')!='ready' or 列表.get('value') is None:
            return
        条数=len(列表['value'].get('entries') or [])
        计数=条数 if 条数>页大小 else 页大小
        自身.起线程(自身.加载,列表['url'],列表['query'],计数,False)

    def 发布详情(自身,键,状态):
        '写下这一键的详情态'
        with 自身.锁:
            下一=dict(自身.详情.getSnapshot())
            下一[键]=状态
            自身.详情.set(下一)

    def 读详情(自身,请求,语言,刷新=False):
        'npm 版本先问注册表比较。npmmirror 最快时带上 npmFileSources'
        键=详情键(请求,语言)
        with 自身.锁:
            自身.详情序号=自身.详情序号+1
            读次=自身.详情序号
            自身.详情读[键]=读次
        自身.发布详情(键,{'status':'loading'})
        远程=自身.上下文.remote
        def 仍是当前():
            '重置或更新的读取会换掉序号'
            return 自身.已拆除 is not True and 自身.详情读.get(键)==读次
        npm文件源=[]
        if 请求.get('npm') is True:
            try:
                最快=等远程(远程.pluginRegistryProbe.fastest())
            except Exception as 探测错误:
                探测错误=None#比较失败则不走 npmmirror
                最快=None
            if isinstance(最快,dict) and 'ok' in 最快:
                最快=最快.get('value') if 最快.get('ok') is True else None
            if 仍是当前() is not True:
                return
            if 最快==npmmirror注册表:
                npm文件源=['npmmirror']
        选项={'refresh':刷新 is True,'npmFileSources':npm文件源}
        def 请求详情():
            '读这一版本的详情文档'
            return 远程.pluginMarket.readEntryDetail(请求['url'],请求['name'],请求['version'],语言,选项)
        应答=自身.询问(请求详情)
        if 仍是当前() is not True:
            return
        if 应答.get('ok') is True:
            自身.发布详情(键,{'status':'ready','detail':应答.get('value')})
        else:
            自身.发布详情(键,{'status':'error','failure':详情失败种类(应答.get('error'))})

    def 读索引(自身):
        '读索引源列表。新添加的源优先成为选中项'
        with 自身.锁:
            自身.索引读=自身.索引读+1
            读次=自身.索引读
            闲=自身.存储.getSnapshot().get('status')=='idle'
        if 闲:
            自身.打补丁({'status':'loading'})
        def 请求列表():
            '列出已配置的索引源'
            return 自身.上下文.remote.pluginMarket.listIndexes()
        应答=自身.询问(请求列表)
        if 自身.已拆除 or 读次!=自身.索引读:
            return
        if 应答.get('ok') is not True:
            自身.打补丁({'status':'error'})
            return
        索引列=应答.get('value') or []
        先前=自身.状态().get('selected')
        最后=索引列[-1] if len(索引列)>0 else None
        with 自身.锁:
            要选新增=自身.选择已添加
            自身.选择已添加=False
        if 要选新增 and 最后 is not None:
            选中=最后['url']
        else:
            选中=None
            for 索引 in 索引列:
                if 索引['url']==先前:
                    选中=先前
            if 选中 is None:
                选中=索引列[0]['url'] if len(索引列)>0 else None
        部分={'status':'ready','indexes':索引列,'selected':选中}
        if len(索引列)==0:
            部分['editing']=False
        自身.打补丁(部分)
        if 选中 is None:
            自身.打补丁({'listing':None})
        elif 选中!=(自身.状态().get('listing') or {}).get('url'):
            自身.加载(选中,初始查询,页大小,False)

    def 加载(自身,网址,查询,计数,刷新):
        '按 Host 接受的页大小凑够条数。文档被替换时整表重读一次'
        with 自身.锁:
            自身.列表读=自身.列表读+1
            读次=自身.列表读
        当前=自身.状态().get('listing')
        if 当前 is not None and 当前.get('url')==网址:
            保留=当前.get('value')
            已答=当前.get('answered')
        else:
            保留=None
            已答=None
        自身.打补丁({'listing':{
            'url':网址,'query':查询,'status':'loading','value':保留,'answered':已答,'failure':None,
        }})
        def 失败态(种类):
            '记下重试动作，并给出错误列表态'
            def 再跑():
                '再读这一次查询'
                自身.加载(网址,查询,计数,刷新)
            自身.失败=再跑
            return {
                'url':网址,'query':查询,'status':'error','value':保留,'answered':已答,'failure':种类,
            }
        值=None
        已重启=False
        while 值 is None or (len(值.get('entries') or [])<计数 and 值.get('nextOffset') is not None):
            偏移=0 if 值 is None else len(值.get('entries') or [])
            上限=计数-偏移
            if 上限>最大页:
                上限=最大页
            取于=None if 值 is None else 值.get('fetchedAt')
            要刷新=刷新 is True and 值 is None and 已重启 is not True
            应答=自身.翻页(网址,查询,偏移,上限,取于,要刷新)
            if 自身.已拆除 or 读次!=自身.列表读:
                return
            if 应答.get('ok') is not True:
                自身.结算(网址,失败态(列表失败种类(应答.get('error'))),应答)
                return
            页=应答.get('value')
            if 值 is None or 页.get('fetchedAt')==值.get('fetchedAt'):
                if 值 is None:
                    值=页
                else:
                    合并=dict(页)
                    合并['entries']=list(值.get('entries') or [])+list(页.get('entries') or [])
                    值=合并
            elif 已重启:
                自身.打补丁({'listing':失败态('changed')})
                return
            else:
                已重启=True
                值=None
        已声明=已声明查询(查询,值.get('metadata') or {})
        if 已声明 is not 查询:
            自身.加载(网址,已声明,计数,False)
            return
        自身.结算(网址,{
            'url':网址,'query':查询,'status':'ready','value':值,'answered':查询,'failure':None,
        },{'ok':True,'value':值})

    def 加载更多(自身):
        '下一页的文档如果换过，就从第一页重载已显示的条数'
        列表=自身.状态().get('listing')
        if 列表 is None:
            return
        if 列表.get('status') not in ('ready','error'):
            return
        if 列表.get('answered')!=列表.get('query'):
            return
        值=列表.get('value')
        if 值 is None or 值.get('nextOffset') is None:
            return
        网址=列表['url']
        查询=列表['query']
        with 自身.锁:
            自身.列表读=自身.列表读+1
            读次=自身.列表读
        下一态=dict(列表)
        下一态['status']='more'
        下一态['failure']=None
        自身.打补丁({'listing':下一态})
        应答=自身.翻页(网址,查询,len(值.get('entries') or []),页大小,值.get('fetchedAt'),False)
        if 自身.已拆除 or 读次!=自身.列表读:
            return
        if 应答.get('ok') is not True:
            def 再跑():
                '再读下一页'
                自身.加载更多()
            自身.失败=再跑
            错误态=dict(列表)
            错误态['status']='error'
            错误态['failure']=列表失败种类(应答.get('error'))
            自身.结算(网址,错误态,应答)
            return
        页=应答.get('value')
        if 页.get('fetchedAt')!=值.get('fetchedAt'):
            自身.加载(网址,查询,len(值.get('entries') or [])+页大小,False)
            return
        合并=dict(页)
        合并['entries']=list(值.get('entries') or [])+list(页.get('entries') or [])
        就绪=dict(列表)
        就绪['status']='ready'
        就绪['value']=合并
        就绪['failure']=None
        自身.结算(网址,就绪,{'ok':True,'value':合并})

    def 翻页(自身,网址,查询,偏移,上限,取于,刷新):
        '把查询收成 Host 的搜索参数'
        体={'sort':查询['sort'],'offset':偏移,'limit':上限}
        if 查询['text'].strip()!='':
            体['text']=查询['text']
        if 查询['category'] is not None:
            体['category']=查询['category']
        if len(查询['labels'])>0:
            体['labels']=list(查询['labels'])
        if 取于 is not None:
            体['fetchedAt']=取于
        if 刷新:
            体['refresh']=True
        def 请求():
            '搜索这一页'
            return 自身.上下文.remote.pluginMarket.search(网址,体)
        return 自身.询问(请求)

    def 结算(自身,网址,列表,应答):
        '发布列表，并把这一次读到的标题或错误写回索引源'
        索引列=[]
        for 索引 in 自身.状态().get('indexes') or []:
            if 索引['url']!=网址:
                索引列.append(索引)
                continue
            if 应答.get('ok') is not True:
                错误=应答.get('error') or {}
                下一=dict(索引)
                下一['error']=错误.get('message')
                索引列.append(下一)
                continue
            值=应答.get('value') or {}
            下一={'url':网址}
            if 值.get('title') is not None:
                下一['title']=值['title']
            if 值.get('description') is not None:
                下一['description']=值['description']
            索引列.append(下一)
        自身.打补丁({'listing':列表,'indexes':索引列})

    def 保存源(自身,网址列,正在添加):
        '保存失败时留下原因并取消“选中新源”'
        自身.打补丁({'saving':True,'sourceFailure':None})
        def 请求():
            '写回索引源列表'
            return 自身.上下文.remote.pluginMarket.setIndexes(网址列)
        应答=自身.询问(请求)
        if 自身.已拆除:
            return
        if 应答.get('ok') is not True:
            with 自身.锁:
                自身.选择已添加=False
            自身.打补丁({'saving':False,'sourceFailure':源失败种类(应答.get('error'))})
            return
        部分={'saving':False}
        if 正在添加:
            部分['draft']=''
        自身.打补丁(部分)
        自身.读索引()
