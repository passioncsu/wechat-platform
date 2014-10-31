# -*- coding: utf-8 -*-

from wechat_sdk import WechatBasic
from wechat_sdk.context.framework.django import DatabaseContextStore, DatabaseContext

from system.core.test import WechatTestCase
from system.official_account.models import OfficialAccount
from system.rule.models import Rule
from system.keyword.models import Keyword
from system.rule_match.models import RuleMatch
from system.request.models import RequestMessage, RequestEvent
from .control import ControlCenter


class ControlCenterTest(WechatTestCase):
    def test_text_flow(self):
        """
        测试文本数据流
        """
        # 初始化固定的OpenID及添加测试上下文数据
        source = self.make_source()
        self.assertEqual(0, DatabaseContext.objects.count())
        context = DatabaseContextStore(openid=source)
        context['test_context'] = u'测试上下文'
        context.save()
        self.assertEqual(1, DatabaseContext.objects.count())

        # 初始化公众号实例及微信请求实例
        official_account = OfficialAccount.manager.add(level=OfficialAccount.LEVEL_3, name='name', email='email@email.com', original='original', wechat='wechat')
        wechat = WechatBasic(token='token')
        wechat.parse_data(data=self.make_raw_text_message(source=source, content=u'乐者为王, that\'s all'))

        # 初始化控制中心并检查初始化是否完全
        control = ControlCenter(official_account=official_account, wechat_instance=wechat)
        self.assertEqual(control.official_account, official_account)
        self.assertEqual(control.wechat, wechat)
        self.assertEqual(control.message, wechat.get_message())
        self.assertEqual(control.context.get('test_context'), u'测试上下文')

        rule = Rule.manager.add(name='rule one', reply_pattern=Rule.REPLY_PATTERN_ALL)
        keyword = Keyword.manager.add(rule=rule, keyword=u'乐者为王', type=Keyword.TYPE_CONTAIN)
        rule_match = RuleMatch.manager.add(rule=rule, plugin_iden='text', reply_id=0)

        response = control.response
        self.assertEqual(1, RequestMessage.objects.count())
        self.assertEqual([{'iden': 'text', 'reply_id': 0}], control.match_plugin_list)