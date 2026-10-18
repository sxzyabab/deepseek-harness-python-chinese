'宿主目录选择的远程拥有者。能力不够的动词直接拒绝，不拿另一种能力去近似'
from ...类型化远程调用.协议 import 远程服务,远程 as 远程装饰#远程服务与方法标记
from .异常 import 远程错误,浏览失败,可取消失败#线路失败

__all__=['目录选择器控制器']

依赖=['directoryPicker']#抽象目录选择缝


class 目录选择器控制器(远程服务):
    '把 ctx.directoryPicker 投影成 directoryPicker 命名空间的线路动词'
    inject=依赖#框架槽

    def __init__(自身,上下文,配置=None):
        '以 directoryPickerController 登记。配置由加载器传入，本服务不读它'
        super().__init__(上下文,'directoryPickerController',{'namespace':'directoryPicker'})#登记

    @远程装饰('pick')
    def pick(自身,信号):
        '打开宿主系统选择器。取消时返回空。信号是调用方寿命'
        能力=自身.要求能力('native','pick')#必须是原生选择
        try:#选择器失败
            return 能力.pick(信号)#绝对路径或空
        except Exception as 错误:#中止或失败
            raise 可取消失败(错误,信号,'directory picker was aborted','directory picker failed')#线路失败

    @远程装饰('list')
    def list(自身,路径,信号):
        '列一层目录。路径省略时列家目录。信号中止后端扫描'
        能力=自身.要求能力('browse','list')#必须能浏览
        try:#列举失败
            return 能力.list(路径,信号)#这一层和祖先
        except Exception as 错误:#中止或浏览失败
            raise 可取消失败(错误,信号,'directory listing was aborted')#线路失败

    @远程装饰('createDirectory')
    def createDirectory(自身,路径,名称):
        '在已有父目录下创建一个单段、非空白的子目录'
        名称合格=isinstance(名称,str) and 名称.strip()!='' and 名称!='.' and 名称!='..' and ('/' not in 名称) and ('\\' not in 名称)#单段
        if (not isinstance(路径,str)) or (not 名称合格):#载荷不合法
            raise 远程错误(
                'gateway/bad-request',
                'invalid payload for host.createDirectory',
                {'issues':[{'message':'host.createDirectory requires a single non-blank path segment name'}]},
            )#拒绝
        能力=自身.要求能力('browse','createDirectory')#必须能浏览
        try:#创建失败
            return 能力.createDirectory(路径,名称)#新目录绝对路径
        except Exception as 错误:#浏览失败
            raise 浏览失败(错误)#线路失败

    def 要求能力(自身,种类,方法名):
        '取出这个动词需要的能力。当前后端种类不对则 directory-picker/unavailable'
        能力=自身.ctx.directoryPicker.capability()#当前后端
        if 能力.kind!=种类:#种类不符
            raise 远程错误(
                'directory-picker/unavailable',
                'directoryPicker.'+方法名+' needs the '+种类+' capability; the composed picker serves "'+str(能力.kind)+'"',
                {'capability':能力.kind},
            )#拒绝
        return 能力#匹配的能力
