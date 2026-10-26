'记住这个浏览器里创建说明有没有被收起'
from ....客户端.存储 import 创建快照存储

__all__=['创建创建信息存储']


def 创建创建信息存储():
    '插件自己的偏好。存储不可用时只是不再记住'
    return 创建快照存储(False,{'persist':{'name':'dsh.creation-recommendations.info-dismissed'}})
