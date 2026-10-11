'宿主配置与浏览器偏好草稿共用的校验'
import re
from .类型 import 思考翻译偏好字段,思考翻译快照字段

__all__=['语言偏好模式','提供方偏好','思考翻译偏好字段','思考翻译快照字段']

语言偏好模式=re.compile(r'^(?:auto|[a-zA-Z]{2,8}(?:-[a-zA-Z0-9]{1,8})*)$')
提供方偏好=('bing','google','deepseek-account','deepseek-official')
