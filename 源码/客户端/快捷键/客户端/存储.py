'显式的浏览器与 Desktop 偏好适配器。Desktop 不回退到浏览器存储'
from types import SimpleNamespace as 简易命名空间#存储读写面与适配器
import pywebbridge#页面上的未定义
from ..协议 import 快捷键持久化#事务协调器

__all__=['快捷键存储键','Web快捷键存储','桌面快捷键存储']

未定义=pywebbridge.基础.undefined#属性缺失
快捷键存储键='dsh.keybindings.v1'#浏览器配置文件与同源本地偏好键

def Web快捷键存储(窗口,平台,发布):
    '把 localStorage 和同源的其他页面更新接到共享事务协调器'
    本地=窗口.localStorage#同源存储

    def 读():
        '读原文'
        return 本地.getItem(快捷键存储键)#没有时是 None

    def 写(原文):
        '整份替换'
        本地.setItem(快捷键存储键,原文)#写入

    持久=快捷键持久化(简易命名空间(read=读,write=写),'web',平台,True,发布)#写前重读

    def 变更(事件):
        '同源其他页面写入或清空时重读'
        键=事件.key#变更键
        if 键 is None or 键==快捷键存储键:#清空或就是这份键
            持久.读当前()#刷新

    窗口.addEventListener('storage',变更)#监听

    def 获取(定义表):
        '安装目录并读当前'
        持久.设定定义(定义表)#目录
        return 持久.读当前()#快照

    def 编辑(编辑,修订):
        '转发一次已核对编辑'
        return 持久.编辑(编辑,修订)#结果

    def 订阅(监听):
        'Web 没有主进程推送'

        def 拆除():
            '没有订阅可卸'
            return None#无事

        return 拆除#拆除器

    def 录制(活跃):
        'Web 没有原生菜单加速器。活跃与桌面桥的签名一致'
        return None#完成

    def 拆除():
        '卸监听并停止接受后续发布'
        窗口.removeEventListener('storage',变更)#卸
        持久.拆除()#停

    return 简易命名空间(
        get=获取,
        edit=编辑,
        subscribe=订阅,
        recording=录制,
        dispose=拆除,
    )

def 桌面快捷键存储(窗口):
    '读当前源的 preload 能力。没有桥时返回 None'
    桌面=窗口['dshDesktop']#preload
    if 桌面 is 未定义 or 桌面 is None:#没有桌面面
        return None#缺桥
    快捷=桌面['shortcuts']#受限 API
    if 快捷 is 未定义 or 快捷 is None:#没有快捷键桥
        return None#缺桥
    return 快捷#桌面适配器
