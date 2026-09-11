"""作曲器键图：菜单裁决、空格裁决、Enter 提交与粘贴路由。

对齐上游 `ui-conversation/src/client/input/editor/keymap.ts`。
公开面仅中文名。处理器为本包对象；IME 组合用纪元毫秒。
根属性 `data-composer-composing` 压住占位符。
"""
import time#纪元毫秒

__all__=['登记作曲器键图']#仅中文公开名

组合宽限毫秒=10#Safari 关闭 keydown 宽限

def 纪元毫秒():
    """墙钟毫秒 int。"""
    return int(time.time()*1000)#纪元毫秒

def 是否组合事件(事件,近期组合):
    """keydown 可信任的组合态。keyCode 229 为无 isComposing 时的遗留 IME 信号。"""
    if 事件['isComposing'] is True:#引擎组合
        return True#是
    if 事件['keyCode']==229:#遗留信号
        return True#是
    return 近期组合() is True#宽限内

def 登记作曲器键图(编辑器,处理器):
    """在一个编辑器上登记作曲器键图。处理器含 arbitrate/space/dismissPopup/canSubmit/submit/intakeFiles/pasteText。"""
    组合中=False#组合中
    组合截止=0#宽限期截止纪元毫秒
    根元素=None#当前根

    def 同步组合():
        """根属性随组合与编辑器对账。"""
        if 根元素 is None:#无根
            return#停
        开=组合中 is True or 编辑器.正在组合() is True#组合中
        根元素.切换属性('data-composer-composing',开)#根属性

    def 组合开始():
        """开始组合。"""
        nonlocal 组合中#写
        组合中=True#开始
        同步组合()#同步

    def 组合结束():
        """结束组合后再一拍宽限。"""
        nonlocal 组合中,组合截止#写
        组合中=False#结束
        组合截止=纪元毫秒()+组合宽限毫秒#宽限
        def 空更新():
            """组合结束后无文档编辑。"""
            return None#无事
        编辑器.更新(空更新,{'onUpdate':同步组合})#提交后再同步

    def 近期组合():
        """组合中或宽限未过。"""
        return 组合中 is True or 纪元毫秒()<组合截止#近期

    def 箭头(键):
        """箭头/Tab 工厂。"""
        def 处理(事件):
            """裁决消费则阻止默认。"""
            在组合=事件 is not None and 是否组合事件(事件,近期组合)#是否组合
            if 处理器.arbitrate(键,在组合)!='pass':#消费
                if 事件 is not None:#有事件
                    事件.阻止默认()#阻止
                return True#已处理
            return False#放行
        return 处理#处理器

    def 根交换(根,旧根):
        """根交换时重挂组合监听。"""
        nonlocal 组合中,组合截止,根元素#写
        if 旧根 is not None:#有旧
            旧根.移除监听('compositionstart',组合开始)#卸 start
            旧根.移除监听('compositionend',组合结束)#卸 end
            旧根.移除属性('data-composer-composing')#卸属性
        组合中=False#清组合
        组合截止=0#清宽限
        根元素=根#记下新根
        if 根 is not None:#有新
            根.添加监听('compositionstart',组合开始)#挂 start
            根.添加监听('compositionend',组合结束)#挂 end
        同步组合()#同步

    def 处理Escape(事件):
        """先解散弹出再裁决。"""
        处理器.dismissPopup()#先关覆盖
        if 处理器.arbitrate('escape',是否组合事件(事件,近期组合))=='consumed':#消费
            事件.阻止默认()#阻止
            return True#已处理
        return False#放行

    def 处理空格(事件):
        """组合中放行；认领则消费。"""
        if 是否组合事件(事件,近期组合) is True:#组合
            return False#放行
        已吃=处理器.space()#空格裁决
        if 已吃 is True:#认领令牌已带尾部分隔
            事件.阻止默认()#阻止
            return True#已处理
        return False#放行

    def 处理回车(事件):
        """Shift+Enter 无条件换行；IME 吞掉；菜单优先；按住不连发。"""
        if 事件 is not None and 事件['shiftKey'] is True:#Shift+Enter
            return False#放行换行
        if 事件 is not None and 是否组合事件(事件,近期组合) is True:#IME 候选
            return True#吞掉，不阻止默认
        if 处理器.arbitrate('enter',False)!='pass':#菜单消费
            if 事件 is not None:#有
                事件.阻止默认()#阻止
            return True#已处理
        if 事件 is not None:#有
            事件.阻止默认()#阻止默认换行
        if 事件 is not None and 事件['repeat'] is True:#按住
            return True#不连发
        if 处理器.canSubmit() is False:#不可提交
            return True#仍吞掉
        加速=事件 is not None and (事件['ctrlKey'] is True or 事件['metaKey'] is True)#Ctrl/Cmd
        处理器.submit(加速)#提交
        return True#已处理

    def 处理粘贴(事件):
        """文件摄入 + 纯文本经壳插入。"""
        剪贴=事件['clipboardData'] if 'clipboardData' in 事件 else None#剪贴板
        if 剪贴 is None:#无
            return False#放行
        文件表=[]#文件
        for 项 in 剪贴['items']:#逐项
            if 项['kind']!='file':#非文件
                continue#下
            文件=项.取文件()#取
            if 文件 is not None:#非空
                文件表.append(文件)#收下
        if len(文件表)>0:#有文件
            处理器.intakeFiles(文件表)#摄入
        文本=剪贴.取数据('text/plain')#纯文本
        if 文本=='':#无文本
            if len(文件表)==0:#皆空
                return False#放行
            事件.阻止默认()#仅文件时阻止
            return True#已处理
        事件.阻止默认()#阻止默认粘贴
        处理器.pasteText(文本)#经壳插入
        return True#已处理

    return 编辑器.合并登记([#拆除器
        编辑器.登记根监听(根交换),#根
        编辑器.登记更新监听(同步组合),#每次更新再同步
        编辑器.登记命令('arrow-up',箭头('up')),#上
        编辑器.登记命令('arrow-down',箭头('down')),#下
        编辑器.登记命令('tab',箭头('tab')),#Tab 仅菜单高亮时作用
        编辑器.登记命令('escape',处理Escape),#Escape
        编辑器.登记命令('space',处理空格),#空格
        编辑器.登记命令('enter',处理回车),#Enter
        编辑器.登记命令('paste',处理粘贴),#粘贴
    ])#合并结束
