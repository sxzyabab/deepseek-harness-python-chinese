"""工作区挑选/添加流程与会话空态挑选器登记。

对齐上游 `ui-workspace/src/client/WorkspacePicker.tsx`。
`工作区挑选流` 为可复用核心（菜单 + 路径错误对话框），由侧栏浏览区同包直连组合；
`工作区选择器` 把主人份额适配到核心流，供会话英雄槽登记。公开面仅中文名。
"""
from .约定.槽位 import 添加工作区令牌#添加令牌

__all__=['工作区挑选流','工作区选择器','样式表']#仅中文公开名

样式表='''#对齐 WorkspacePicker.module.css
.menuStatus{padding:8px 12px;color:var(--dsw-alias-label-tertiary);font-size:13px;line-height:20px}
.modalAction{min-width:88px}
.modalError{color:var(--dsw-alias-state-error-primary);font-size:13px;line-height:20px;white-space:pre-wrap}
'''#样式表结束

class 工作区挑选流:#菜单 + 路径错误对话框
    """渲染挑选菜单与采纳错误对话框；目录流由占位者填入。"""
    def __init__(自身,属性):#流 props
        """记下翻译、开关、工作区钩、创建与目录流渲染。"""
        自身.翻译=属性['t']#文案
        自身.打开=属性['open']#弹出开关
        自身.锚点引用=属性['anchorRef'] if 'anchorRef' in 属性 else None#锚点
        自身.用工作区=属性['useWorkspaces']#工作区列表钩
        自身.创建工作区=属性['createWorkspace']#创建回调
        自身.用目录流=属性['useDirectoryFlow'] if 'useDirectoryFlow' in 属性 else None#占用钩
        自身.渲染目录流=属性['renderDirectoryFlow'] if 'renderDirectoryFlow' in 属性 else None#渲染孔
        自身.已选标识=属性['selectedId'] if 'selectedId' in 属性 else None#当前选中
        自身.挑选=属性['onPick']#挑中回调
        自身.关闭=属性['onClose']#关闭弹出
        自身.仅添加=属性['addOnly'] is True if 'addOnly' in 属性 else False#仅添加
        自身.侧边=属性['side'] if 'side' in 属性 and 属性['side'] is not None else 'bottom'#弹出方向
        自身.错误打开=False#错误对话框
        自身.对话框错误=None#错误文案
        自身.流打开=False#目录流请求
        自身.挑选文件夹中=False#采纳进行中

    def 流忙碌(自身):#流是否占用表面
        """目录流打开或采纳进行中。"""
        return 自身.流打开 or 自身.挑选文件夹中#忙碌

    def 流可用(自身):#孔是否被占用
        """目录流孔占用态。"""
        if 自身.用目录流 is None:#无钩
            return False#不占用
        def 选占用(占用):#选择器身份
            """占用态。"""
            return 占用#原样
        return 自身.用目录流(选占用)#占用

    def 关闭对话框(自身):#关掉错误对话框
        """清错误态。"""
        自身.错误打开=False#关
        自身.对话框错误=None#清

    def 采纳目录(自身,路径):#采纳已选路径
        """创建工作区；失败落入错误对话框。"""
        try:#创建
            工作区=自身.创建工作区({'path':路径})#创建；返回操作任务
            工作区=工作区.等待()#等待
            自身.流打开=False#关流
            自身.挑选(工作区['workspaceId'])#挑中
        except Exception as 原因:#失败；创建路径 RPC 异常契约未定，故不能换成更窄的 except
            自身.对话框错误=str(原因)#错误文案
            自身.流打开=False#关流
            自身.错误打开=True#开对话框

    def 打开目录流(自身):#拉起目录流
        """关掉弹出并请求目录流。"""
        自身.关闭()#关弹出
        自身.错误打开=False#清对话框
        自身.对话框错误=None#清文案
        自身.流打开=True#开流

    def 流主人(自身):#目录流主人份额
        """open/busy/onPicked/onCancel/onError。"""
        def 已选(路径):#选中目录
            """采纳路径。"""
            自身.挑选文件夹中=True#忙碌
            try:#采纳
                自身.采纳目录(路径)#采纳
            finally:#无论成败
                自身.挑选文件夹中=False#清忙碌
        def 取消流():#取消
            """关流。"""
            自身.流打开=False#关
        def 流失败(消息):#失败
            """开错误对话框。"""
            自身.流打开=False#关流
            自身.对话框错误=消息#文案
            自身.错误打开=True#开对话框
        return {#主人份额
            'open':自身.流打开,#是否请求
            'busy':自身.挑选文件夹中,#采纳中
            'onPicked':已选,#选中
            'onCancel':取消流,#取消
            'onError':流失败,#失败
        }#份额结束

    def 处理选择(自身,标识):#菜单选择
        """添加令牌拉起流，否则挑中工作区。"""
        if 标识==添加工作区令牌:#添加
            自身.打开目录流()#开流
            return#已处理
        自身.挑选(标识)#挑中工作区

    def 渲染(自身):#结构树
        """返回菜单 + 目录流孔 + 错误对话框。"""
        if 自身.流打开 and not 自身.流可用():#占位者中途卸载
            自身.流打开=False#撤回流
        def 原样(状态):#选择器身份
            """整表。"""
            return 状态#快照
        快照=自身.用工作区(原样) if 自身.用工作区 is not None else {'items':[],'phase':'ready'}#工作区快照
        工作区列表=快照['items'] if 'items' in 快照 and 快照['items'] is not None else []#列表
        添加条目=[{'id':添加工作区令牌,'label':自身.翻译('menu.addWorkspace'),'disabled':自身.流忙碌()}] if 自身.流可用() else []#添加行
        钉住添加=(not 自身.仅添加) and len(工作区列表)>0#钉在页脚
        if 钉住添加:#列表 + 页脚添加
            条目=[{'id':区['workspaceId'],'label':区['title'],'disabled':自身.流忙碌()} for 区 in 工作区列表]#工作区行
        else:#仅添加
            条目=添加条目#添加行
        菜单空=len(条目)==0#空菜单
        列表已定=自身.仅添加 or 快照['phase']=='ready'#基线落地
        添加即唯一=(not 钉住添加) and 列表已定 and len(添加条目)==1#锚点即添加
        if 自身.打开 and 添加即唯一 and not 自身.流忙碌():#锚点直接开流
            自身.打开目录流()#开流
        return {#结构树
            'type':'fragment',#片段
            'children':[#子树
                {'type':'Menu','open':自身.打开 and not 添加即唯一 and not 菜单空,'items':条目,'footer':添加条目 if 钉住添加 else None,'selectedId':自身.已选标识,'onSelect':'select','onClose':'close','side':自身.侧边},#菜单
                {'type':'div','class':'menuStatus','role':'status','children':[自身.翻译('picker.loading')]} if 自身.打开 and not 添加即唯一 and not 菜单空 and 快照['phase']=='pending' else None,#加载态
                自身.渲染目录流(自身.流主人()) if 自身.渲染目录流 is not None else None,#目录流孔
                {'type':'Modal','open':自身.错误打开,'onClose':'closeModal','title':自身.翻译('folderError.title'),'children':[{'type':'div','class':'modalError','role':'alert','children':[自身.对话框错误]}],'footer':[{'type':'Button','variant':'outline','class':'modalAction','onClick':'closeModal','label':自身.翻译('cancel')},{'type':'Button','variant':'primary','class':'modalAction','disabled':not 自身.流可用(),'onClick':'retry','label':自身.翻译('folderError.retry')}]},#错误对话框
            ],#子树结束
        }#结构树结束

    def 处理动作(自身,动作,载荷=None):#分发交互
        """菜单选择、关闭、重试。"""
        if 动作=='select':#菜单选择
            自身.处理选择(载荷)#处理
            return#已处理
        if 动作=='close':#关弹出
            自身.关闭()#回调
            return#已处理
        if 动作=='closeModal':#关对话框
            自身.关闭对话框()#清
            return#已处理
        if 动作=='retry':#重新选择
            自身.打开目录流()#开流

class 工作区选择器:#会话空态登记
    """把主人份额适配到核心挑选流。"""
    def __init__(自身,属性):#空态槽 props
        """记下主人份额与注入创建回调。"""
        自身.属性=属性#完整 props

    def 渲染(自身):#结构树
        """返回挑选流结构树。"""
        属性=自身.属性#props
        def 渲目录流(主人):#渲染孔
            """英雄目录流槽。"""
            return 属性['renderSlot']('conversation.hero.workspace.directoryFlow',主人)#孔
        流=工作区挑选流({#核心流 props
            't':属性['t'],#文案
            'open':属性['open'],#开关
            'anchorRef':属性['anchorRef'] if 'anchorRef' in 属性 else None,#锚点
            'useWorkspaces':属性['useWorkspaces'],#工作区钩
            'createWorkspace':属性['createWorkspace'],#创建
            'useDirectoryFlow':属性['useDirectoryFlow'] if 'useDirectoryFlow' in 属性 else None,#占用钩
            'renderDirectoryFlow':渲目录流,#渲染孔
            'selectedId':属性['selectedId'] if 'selectedId' in 属性 else None,#选中
            'onPick':属性['onPick'],#挑中
            'onClose':属性['onClose'],#关闭
        })#流结束
        return 流.渲染()#结构树
