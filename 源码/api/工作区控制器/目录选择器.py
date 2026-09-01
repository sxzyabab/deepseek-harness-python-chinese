"""宿主目录选择 Remote 拥有者。

对齐上游 `workspace-controller/src/directory-picker.ts`。公开面仅中文名。
"""
import re#路径段校验
from ...typert.协议 import 远程服务,远程 as _远程#Remote 基类
from .工具 import 取字段,解开,远程错误,远程错误消息,信号已中止#辅助

__all__=['目录选择器控制器']#仅中文公开名

创建目录请求名形态=re.compile(r'^[^/\\]+$')#单段名

浏览失败码表={#seam → wire
    'directory-unreadable':'directory-picker/unreadable',
    'directory-exists':'directory-picker/exists',
    'directory-create-failed':'directory-picker/create-failed',
}#结束

class 目录选择器控制器(远程服务):#目录选择 Remote 服务
    """把抽象 directoryPicker 缝投影到 wire 动词。"""
    注入=['directoryPicker']#依赖后端

    def __init__(自身,上下文):#构造
        """登记 directoryPickerController 命名空间。"""
        super().__init__(上下文,'directoryPickerController',{'namespace':'directoryPicker'})#注册

    @_远程('pick')
    def pick(自身,信号):#原生选择
        """打开 OS 选择器。"""
        能力=自身._要求能力('native','pick')#必须 native
        try:#调用
            return 解开(能力.pick(信号))#结果
        except Exception as 错误:#失败
            raise 自身._可取消失败(错误,信号,'directory picker was aborted','directory picker failed')#映射

    @_远程('list')
    def list(自身,路径,信号):#列目录
        """列一层目录。"""
        能力=自身._要求能力('browse','list')#必须 browse
        try:#调用
            return 解开(能力.list(路径,信号))#列表
        except Exception as 错误:#失败
            raise 自身._可取消失败(错误,信号,'directory listing was aborted')#映射

    @_远程('createDirectory')
    def createDirectory(自身,路径,名称):#建子目录
        """创建单段子目录。"""
        名=str(名称 or '').strip()#去空白
        if 名=='' or 名=='.' or 名=='..' or (not 创建目录请求名形态.match(名)):#非法
            raise 远程错误('gateway/bad-request','invalid payload for host.createDirectory',{'issues':[{'message':'host.createDirectory requires a single non-blank path segment name'}]})#拒绝
        能力=自身._要求能力('browse','createDirectory')#必须 browse
        try:#调用
            return 解开(能力.createDirectory(路径,名))#路径
        except Exception as 错误:#失败
            raise 自身._浏览失败(错误)#映射

    def _要求能力(自身,种类,方法名):#解析能力
        """取所需能力或拒绝。"""
        能力=自身.ctx.directoryPicker.capability()#当前能力
        if 取字段(能力,'kind')!=种类:#种类不符
            raise 远程错误('directory-picker/unavailable','directoryPicker.'+方法名+' needs the '+种类+' capability; the composed picker serves "'+str(取字段(能力,'kind'))+'"',{'capability':取字段(能力,'kind')})#拒绝
        return 能力#返回能力对象

    def _浏览失败(自身,错误):#浏览失败映射
        """把 seam 错误投影到 directory-picker/*。"""
        码=getattr(错误,'code',None)#seam 码
        if 码 in 浏览失败码表:#已知
            return 远程错误(浏览失败码表[码],远程错误消息(错误),{'path':getattr(错误,'path',None)},cause=错误)#映射
        return 远程错误('gateway/internal',远程错误消息(错误),{},cause=错误)#内部

    def _可取消失败(自身,错误,信号,取消文案,失败前缀=None):#可取消失败
        """中止优先于业务失败。"""
        if 信号已中止(信号):#已取消
            return 远程错误('gateway/cancelled',取消文案,{},cause=错误)#取消
        if 失败前缀 is None:#浏览动词
            return 自身._浏览失败(错误)#浏览映射
        return 远程错误('gateway/internal',失败前缀+': '+远程错误消息(错误),{},cause=错误)#内部
