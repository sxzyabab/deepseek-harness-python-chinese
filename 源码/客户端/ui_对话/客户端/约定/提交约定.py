"""输入域与设置域共用的 composer 提交词汇。

对齐上游 `ui-conversation/src/client/contract/composer-submission.ts`。公开面仅中文名。
"""
from ...提交设置 import 忙碌回车行为表,默认忙碌回车行为#忙碌 Enter

__all__=['输入提交模式','提交手势','忙碌回车行为表','默认忙碌回车行为']#仅中文公开名

输入提交模式=忙碌回车行为表#普通消息投递模式等同忙碌 Enter
提交手势=('enter','accelerated')#Enter 或加速手势
