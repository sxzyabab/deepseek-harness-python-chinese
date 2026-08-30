"""逐条消息反馈控件：赞/踩 + 可选说明。



对齐上游 `ui-message-feedback/src/client/MessageFeedbackActions.tsx`。公开面仅中文名。

"""



__all__=['消息反馈动作']#仅中文公开名

import threading#后台观察动作结果



def 取字段(对象,键,缺省=None):#从映射或对象读字段

    """从映射或对象读字段，缺席为缺省。"""

    if 对象 is None:#空

        return 缺省#缺席

    if isinstance(对象,dict):#映射

        if 键 in 对象:#自有键

            return 对象[键]#值

        return 缺省#缺席

    return getattr(对象,键,缺省)#属性



class 消息反馈动作:#一条消息的反馈控件

    """赞/踩对 + 可选说明编辑器。"""

    def __init__(自身,属性):#按合成 props 构造

        """记下 props。"""

        自身.属性=属性#合成 props

        自身.说明打开=False#说明编辑器

        自身.草稿=''#说明草稿

        自身.进行中=False#动作进行中

        自身.失败=None#失败文案

        自身.已播种=False#是否已 ensure

        自身.存活=True#实例是否仍挂载



    def 更新(自身,属性):#props 变更

        """刷新合成 props。"""

        自身.属性=属性#最新



    def 卸载(自身):#卸载

        """标死。"""

        自身.存活=False#死



    def 播种(自身):#首次交互加载

        """Session 反馈只读一次。"""

        if 自身.已播种:#已播种

            return#跳过

        自身.已播种=True#记下

        确保=取字段(自身.属性,'ensure')#ensure

        if 确保 is not None:#有

            确保()#加载



    def 结算(自身,结果):#动作结算

        """更新进行中与失败文案。"""

        if not 自身.存活:#已死

            return#丢弃

        自身.进行中=False#结束

        if 取字段(结果,'ok'):#成功

            自身.失败=None#清

            return#结束

        翻译=取字段(自身.属性,'t',lambda 键,_=None:键)#文案

        码=取字段(取字段(结果,'error'),'code')#错误码

        自身.失败=翻译('error.conflict') if 码=='version-conflict' else 翻译('error.generic')#文案



    def 评分(自身,下一):#点赞/踩

        """走 toggle。"""

        自身.播种()#确保已读

        自身.进行中=True#进行中

        自身.失败=None#清

        自身.说明打开=False#关说明

        切换=取字段(自身.属性,'toggle')#toggle

        消息标识=取字段(自身.属性,'messageId')#消息 id

        结果=切换(消息标识,下一) if 切换 is not None else {'ok':True}#切换

        if hasattr(结果,'wait') or hasattr(结果,'等待'):#可等待

            def 观察():#观察切换

                try:#等待

                    自身.结算(结果.wait() if hasattr(结果,'wait') else 结果.等待())#结算

                except BaseException as 错误:#失败

                    自身.结算({'ok':False,'error':{'code':'transport','message':str(错误)}})#折成形

            threading.Thread(target=观察,daemon=True).start()#挂观察

        else:#同步

            自身.结算(结果)#结算



    def 保存说明(自身,当前评价):#保存说明

        """空草稿走 clearNote。"""

        修剪=自身.草稿.strip()#修剪

        自身.进行中=True#进行中

        自身.失败=None#清

        消息标识=取字段(自身.属性,'messageId')#消息 id

        if 修剪=='':#空

            结算=取字段(自身.属性,'clearNote')(消息标识)#清说明

        else:#有内容

            结算=取字段(自身.属性,'rate')(消息标识,当前评价,修剪)#写入

        def 完成(结果):#结算后关编辑器

            """成功则关闭。"""

            自身.结算(结果)#结算

            if 取字段(结果,'ok') and 自身.存活:#成功且存活

                自身.说明打开=False#关

        if hasattr(结算,'wait') or hasattr(结算,'等待'):#可等待

            def 观察():#观察保存

                try:#等待

                    完成(结算.wait() if hasattr(结算,'wait') else 结算.等待())#完成

                except BaseException as 错误:#失败

                    完成({'ok':False,'error':{'code':'transport','message':str(错误)}})#折成形

            threading.Thread(target=观察,daemon=True).start()#挂观察

        else:#同步

            完成(结算)#完成



    def 视图(自身):#读视图模型

        """赞/踩状态与说明编辑器。"""

        用反馈=取字段(自身.属性,'useFeedback')#选择器

        消息标识=取字段(自身.属性,'messageId')#消息 id

        翻译=取字段(自身.属性,'t',lambda 键,_=None:键)#文案

        if 用反馈 is None:#无

            项=None#无条目

            加载失败=False#无

        else:#有

            项=用反馈(lambda 视:取字段(取字段(视,'items'),消息标识) if isinstance(取字段(视,'items'),dict) else (取字段(视,'items').get(消息标识) if hasattr(取字段(视,'items'),'get') else None))#条目

            加载失败=用反馈(lambda 视:取字段(视,'status')=='error')#加载失败

        评价=取字段(项,'rating')#评价

        return {#视图

            'rating':评价,#评价

            'noteOpen':自身.说明打开,#说明开闭

            'draft':自身.草稿,#草稿

            'pending':自身.进行中,#进行中

            'failure':自身.失败 or (翻译('error.load') if 加载失败 else None),#失败

            'likeLabel':翻译('action.likeActive') if 评价=='positive' else 翻译('action.like'),#赞标签

            'dislikeLabel':翻译('action.dislikeActive') if 评价=='negative' else 翻译('action.dislike'),#踩标签

            'note':取字段(项,'note'),#已存说明

        }#视图结束



    def __call__(自身,属性=None):#组件调用形

        """对齐 React 组件调用；返回视图。"""

        if 属性 is not None:#有新 props

            自身.更新(属性)#刷新

        return 自身.视图()#视图


