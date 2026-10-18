'单条文件引用自己画出芯片，并收住同步打开失败'
from ...模块.客户端.通告 import 取握手窗口
from ...ui_基础界面组件.按钮 import 按钮#关闭与重试
from ...ui_基础界面组件.模态 import 模态#失败对话框
from ...ui_基础界面组件.用户文本 import 引用芯片#行内芯片

__all__=['文件引用','文件夹引用']

class 文件引用:
    '文件芯片。能点时按会话打开，失败只留在这一条上'
    def __init__(自身,属性=None):
        '记下节点。有节点就画出芯片'
        自身.属性=属性 if isinstance(属性,dict) else {}#props
        自身.失败路径=None#还没失败
        自身.根=None#芯片节点
        自身.对话框=None#失败对话框
        if 'node' in 自身.属性:#有引用数据
            自身.渲染()#画出

    def 渲染(自身):
        '画出文件芯片。打开失败时把对话框挂到文档上'
        属性=自身.属性#当前 props
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#宿主窗口
        文档=窗口.document#文档
        节点=属性['node']#文本节点
        数据=节点['data']#路径与标签
        路径=数据['path']#解码后的路径
        标签=数据['label']#芯片文字
        原文=属性.get('raw')#原文拼写
        可交互=bool(属性.get('interactive'))#允许打开
        旧=自身.根#上一只芯片
        父=None#挂载点
        if 旧 is not None:#先拆旧芯片
            父=旧.parentNode#记住位置
            旧.remove()#拆掉
        芯片属性={#交给引用芯片
            'window':窗口,#窗口
            'appearance':'file',#文件外观
            'label':标签,#标签
            'title':'' if 原文 is None else str(原文),#原文作标题
        }#芯片属性结束
        if 可交互:#可打开才接激活
            芯片属性['onActivate']=自身.打开#点芯片即打开
        根=引用芯片(芯片属性).渲染()#芯片节点
        自身.根=根#留下
        if 父 is None and 'parent' in 属性 and 属性['parent'] is not None:#宿主指定父节点
            父=属性['parent']#用它
        if 父 is not None and 根 is not None and 根.parentNode is not 父:#还没挂上
            父.appendChild(根)#挂上
        if 自身.对话框 is not None:#先拆旧对话框
            自身.对话框.remove()#拆掉
            自身.对话框=None#清空
        if 可交互 and 自身.失败路径==路径:#这一条还停在失败上
            关钮=按钮({#关闭
                'window':窗口,#窗口
                'variant':'outline',#线框
                'onClick':自身.关闭,#关掉提示
                'children':'关闭',#关闭
            })#关闭按钮
            重试钮=按钮({#重试
                'window':窗口,#窗口
                'variant':'primary',#主按钮
                'onClick':自身.打开,#再打开一次
                'children':'重试',#重试
            })#重试按钮
            对话框=模态({#失败提示
                'window':窗口,#窗口
                'open':True,#打开
                'onClose':自身.关闭,#关掉
                'closeLabel':'关闭',#关闭
                'title':'无法打开文件',#标题
                'description':'无法打开“'+str(路径)+'”，请重试或关闭此提示',#说明
                'footer':[关钮,重试钮],#页脚
                'parent':文档.body,#挂到文档
            })#对话框属性结束
            自身.对话框=对话框.渲染()#画出
        return 根#芯片

    def 打开(自身):
        '按来源会话打开。失败只留下这一条的提示'
        属性=自身.属性#当前 props
        节点=属性['node']#文本节点
        数据=节点['data']#路径与标签
        路径=数据['path']#要打开的路径
        try:#同步打开
            属性['openFile'](路径)#交给注入的打开
        except Exception:#打开失败，句子用固定中文，不用错误原文
            自身.失败路径=路径#记下失败路径
            自身.渲染()#留下对话框
            return#停在失败
        自身.失败路径=None#打开成功
        自身.渲染()#收起对话框

    def 关闭(自身):
        '关掉这一条的失败提示，芯片还在'
        自身.失败路径=None#清掉失败
        自身.渲染()#收起对话框

    def __call__(自身,属性=None):
        '再次交给槽位时按新 props 重画'
        if 属性 is not None:#有新 props
            自身.属性=属性 if isinstance(属性,dict) else {}#换上
        return 自身.渲染()#重画

class 文件夹引用:
    '目录只显示标签，即使周围的文字允许打开文件'
    def __init__(自身,属性=None):
        '记下节点。有节点就画出芯片'
        自身.属性=属性 if isinstance(属性,dict) else {}#props
        自身.根=None#芯片节点
        if 'node' in 自身.属性:#有引用数据
            自身.渲染()#画出

    def 渲染(自身):
        '画出不可点的目录芯片'
        属性=自身.属性#当前 props
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#宿主窗口
        节点=属性['node']#文本节点
        数据=节点['data']#路径与标签
        标签=数据['label']#芯片文字
        原文=属性.get('raw')#原文拼写
        旧=自身.根#上一只芯片
        父=None#挂载点
        if 旧 is not None:#先拆旧芯片
            父=旧.parentNode#记住位置
            旧.remove()#拆掉
        根=引用芯片({#目录芯片
            'window':窗口,#窗口
            'appearance':'folder',#目录外观
            'label':标签,#标签
            'title':'' if 原文 is None else str(原文),#原文作标题
        }).渲染()#芯片节点
        自身.根=根#留下
        if 父 is None and 'parent' in 属性 and 属性['parent'] is not None:#宿主指定父节点
            父=属性['parent']#用它
        if 父 is not None and 根 is not None and 根.parentNode is not 父:#还没挂上
            父.appendChild(根)#挂上
        return 根#芯片

    def __call__(自身,属性=None):
        '再次交给槽位时按新 props 重画'
        if 属性 is not None:#有新 props
            自身.属性=属性 if isinstance(属性,dict) else {}#换上
        return 自身.渲染()#重画
