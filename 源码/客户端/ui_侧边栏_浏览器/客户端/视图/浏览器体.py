from ..浏览器.导航 import 浏览器导航#导航

__all__=['浏览器体','网页沙箱令牌']#仅中文公开名

网页沙箱令牌='allow-scripts allow-forms allow-same-origin allow-popups allow-popups-to-escape-sandbox'#固定 Web iframe sandbox
_初帧={'document':None,'sandboxed':True,'loadFailed':False}#缺省帧态

def 失败文案(原因,翻译):
    """把解析拒因翻成展示句，不在逻辑里匹配展示串。"""
    return 翻译(f'error.{原因}')#文案键

class 浏览器体:#浏览器正文视图模型
    """控制器拥有的 URL 状态与 Web iframe 载体的标签渲染。"""
    def __init__(自身,属性):
        """记下合成 props。"""
        自身.属性=属性#props
        自身.草稿=None#地址草稿
        自身.草稿修订=None#草稿绑定修订
        自身.挂载次数=0#挂载代数
        自身.初态=None#首次快照
        自身.初址=None#可选初始 URL

    def 更新(自身,属性):
        """刷新合成 props。"""
        自身.属性=属性#最新

    def 视图(自身):
        """投影浏览器体视图模型。"""
        属性=自身.属性#props
        翻译=属性['t']#文案
        标签=属性['useTabInfo']()['tab']#标签
        def 选标签桶(快照):
            """按标签取持久化桶。"""
            if 标签['id'] not in 快照['byTab']:#无
                return None#空
            return 快照['byTab'][标签['id']]#桶
        存=属性['useStore'](选标签桶)#按标签
        状态=浏览器导航.空() if 存 is None else 存#状态
        if 自身.初态 is None:#首次
            自身.初态=状态#记下
            参数=标签['navigation']['params'] if 'navigation' in 标签 and 'params' in 标签['navigation'] else None#参数
            自身.初址=参数['url'] if 参数 is not None and 'url' in 参数 else None#初址
        当前=浏览器导航.当前(状态)#当前条目
        请求=状态['request']#请求
        修订=请求['revision'] if 请求 is not None else None#修订
        受控=当前['url'] if 当前 is not None else 自身.初址#受控址
        if 自身.草稿 is not None and 自身.草稿修订==修订:#草稿有效
            草稿=自身.草稿#草稿
        else:#跟受控
            草稿=受控 if 受控 is not None else ''#草稿
        帧源=属性['useBrowserFrame'](标签['id']) if 'useBrowserFrame' in 属性 else None#帧
        帧=_初帧 if 帧源 is None else 帧源.取快照()#帧态
        文档=帧['document']#文档
        沙箱=帧['sandboxed']#沙箱
        加载失败=帧['loadFailed']#失败
        未知=状态['navigation']['status']=='unknown'#未知导航
        外链=None if 未知 else (当前['url'] if 当前 is not None else None)#外链
        失败=None if 状态['failure'] is None else 失败文案(状态['failure']['reason'],翻译)#失败句
        占位=翻译('start') if 当前 is None else 翻译('loading')#占位
        def 后退():
            """后退。"""
            属性['goBack'](标签['id'])#退
        def 前进():
            """前进。"""
            属性['goForward'](标签['id'])#进
        def 刷新():
            """刷新。"""
            属性['reload'](标签['id'])#刷
        def 切换沙箱():
            """切换沙箱。"""
            属性['toggleSandbox'](标签['id'])#沙箱
        def 报告已加载():
            """报告已加载。"""
            if 文档 is not None:属性['reportLoaded'](标签['id'],文档['revision'])#已加载
        def 报告加载失败():
            """报告加载失败。"""
            if 文档 is not None:属性['reportLoadFailed'](标签['id'],文档['revision'])#失败
        return {#视图
            'kind':'browser-body',#种类
            'draft':草稿,#草稿
            'cssModule':'浏览器.module.css',#样式
            'sandboxToken':网页沙箱令牌,#sandbox
            'sandboxed':沙箱,#沙箱开
            'loadFailed':加载失败,#加载失败
            'failure':失败,#地址失败文案
            'placeholder':占位,#占位
            'document':文档,#文档
            'navigationUnknown':未知,#未知
            'externalUrl':外链,#外链
            'canGoBack':浏览器导航.可后退(状态),#可退
            'canGoForward':浏览器导航.可前进(状态),#可进
            'canReload':当前 is not None,#可刷
            'labels':{#控件文案
                'back':翻译('back'),
                'forward':翻译('forward'),
                'reload':翻译('reload'),
                'go':翻译('go'),
                'external':翻译('external'),
                'address':翻译('address.placeholder'),
                'addressChanged':翻译('address.changed'),
                'sandbox':翻译('sandbox.disable' if 沙箱 else 'sandbox.enable'),
                'sandboxWarning':翻译('sandbox.warning'),
                'loadFailed':翻译('web.loadFailed'),
                'unknown':翻译('web.unknown'),
            },#文案结束
            'actions':{#动作
                'setDraft':自身.设草稿,#改草稿
                'submit':自身.提交,#提交
                'goBack':后退,#后退
                'goForward':前进,#前进
                'reload':刷新,#刷新
                'toggleSandbox':切换沙箱,#沙箱
                'reportLoaded':报告已加载,#已加载
                'reportLoadFailed':报告加载失败,#失败
            },#动作结束
        }#视图结束

    def 设草稿(自身,文本):
        """更新地址草稿。"""
        属性=自身.属性#props
        标签=属性['useTabInfo']()['tab']#标签
        def 选标签桶(快照):
            """按标签取持久化桶。"""
            if 标签['id'] not in 快照['byTab']:#无
                return None#空
            return 快照['byTab'][标签['id']]#桶
        存=属性['useStore'](选标签桶)#状态
        状态=浏览器导航.空() if 存 is None else 存#状态
        请求=状态['request']#请求
        自身.草稿修订=请求['revision'] if 请求 is not None else None#绑定
        自身.草稿=文本#草稿

    def 提交(自身):
        """提交地址栏。"""
        属性=自身.属性#props
        标签=属性['useTabInfo']()['tab']#标签
        视图=自身.视图()#当前
        属性['loadUrl'](标签['id'],视图['draft'])#加载

    def 确保挂载(自身):
        """首次渲染时挂载控制器并按初态恢复。"""
        属性=自身.属性#props
        标签=属性['useTabInfo']()['tab']#标签
        if 自身.挂载次数==0:#首次
            应用源=属性['applicationOrigin'] if 'applicationOrigin' in 属性 else None#应用源
            属性['mount'](标签['id'],标签['signal'],应用源,自身.初态)#挂载
            自身.挂载次数=1#已挂
            恢复=浏览器导航.当前(自身.初态)#恢复
            if 恢复 is not None:#有历史
                属性['reload'](标签['id'])#刷新
            elif 自身.初址 is not None:#有初址
                属性['loadUrl'](标签['id'],自身.初址)#加载
