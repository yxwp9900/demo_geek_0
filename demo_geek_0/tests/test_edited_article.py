import time
from copy import deepcopy
from datetime import datetime

from nose import tools
import json

from tests import test_app, user_data, edited_data, article_data, BaseTest
from geek_digest.model import RawArticle, EditedArticle, User
from geek_digest.common.constant import EditedAriticleConstant

news = [{'title': '中兴终端CEO程立新离职', 'source': 'cnbeta',
         'url': 'http://www.cnbeta.com/articles/tech/744077.htm',
         'date': 1530949320, 'source_cn': 'cnBeta'}]


class TestEditedArticle(BaseTest):
    @classmethod
    def setup_class(cls):
        cls.test_data = deepcopy(user_data)
        cls.test_data['level'] = 9
        cls.article_data = deepcopy(article_data)
        cls.edited_data = deepcopy(edited_data)
        cls.edited_id_list = []
        cls.test_login(cls.test_data)
        cls.__test_save_raw_article()
        cls.__test_save_edited_article()

    @classmethod
    def teardown_class(cls):
        cls.clean_user()
        for id in cls.edited_id_list:
            edited_article = EditedArticle.objects(id=id).first()
            if edited_article:
                edited_article.delete()
        RawArticle.get_by_id(cls.raw_id).delete()

    @classmethod
    def __test_save_raw_article(cls):
        raw_article = RawArticle(**cls.article_data)
        raw_article.save()
        cls.raw_id = raw_article.id

    @classmethod
    def __test_save_edited_article(cls):
        for i in range(25):
            edited_article = EditedArticle(**cls.edited_data)
            edited_article.creator = cls.user
            edited_article.url = edited_article.url + str(i)
            edited_article.save()
            cls.edited_id_list.append(edited_article.id)

    @tools.nottest
    def test_news_api_detail(self):
        a_id = self.edited_id_list[-1]
        ariticle = EditedArticle.get_by_id(a_id)
        response = test_app.get(f'/api/v1/news/{a_id}')
        json_resp = self.validate_response(response, 200)
        tools.assert_equals(json_resp.get('data'),
                            ariticle.api_response())

        ariticle.state = EditedAriticleConstant.STATE_PENDING
        ariticle.save()
        ariticle.reload()

        response = test_app.get(f'/api/v1/news/{a_id}')
        json_resp = self.validate_response(response, 403)

    @tools.nottest
    def test_news_published(self, amount, json_resp):
        for i in range(amount - 1):
            latest_publish = json_resp['data']['list'][i]['published']
            last_publish = json_resp['data']['list'][i + 1]['published']
            if last_publish > latest_publish:
                return False
            return True

    def test_news_api(self):
        """
        测试news的get接口

        1、测试能否查询到所有published状态的文章
        2、测试查询结果的分页功能
        3、测试新闻是否按published排序
        """
        query = {'state': EditedAriticleConstant.STATE_PUBLISHED}
        response = test_app.get('api/v1/news')
        json_resp = self.validate_response(response, 200)
        tools.assert_equals(json_resp['data']['count'], 25)

        EditedArticle.objects().update(
            state=EditedAriticleConstant.STATE_PUBLISHED)

        length = EditedArticle.objects(**query).count()
        response = test_app.get('api/v1/news')

        json_resp = self.validate_response(response, 200)
        tools.assert_equals(json_resp['data']['count'], length)
        tools.assert_true(self.test_news_published(length, json_resp))
        tools.assert_true(length > 20)
        tools.assert_equals(len(json_resp['data']['list']), 20)
        json_item = json_resp['data']['list'][0]
        item = EditedArticle.get_by_id(id=json_item['id'])
        tools.assert_equals(json_item, item.api_base_response())
        article_count = EditedArticle.objects(state='published').count()
        self.test_search('news', article_count)

    def test_search_day(self):
        """
        测试查询某一天的文章

        1、测试查询没有文章的一天，结果为0
        2、测试查询某一天文章
        3、测试查询结果的分页功能
        4、测试查询结果是否按published排序
        """
        __time = datetime.now()
        day_str = __time.strftime('%Y%m%d')
        headers = {'Authorization': self.token}
        response = test_app.get('api/v1/news?day=20100101',
                                headers=headers)
        json_resp = self.validate_response(response)
        tools.assert_equals(json_resp['data']['count'], 0)

        response = test_app.get(f'api/v1/news?day={day_str}',
                                headers=headers)
        length = EditedArticle.objects(state='published').count()
        json_resp = self.validate_response(response)
        tools.assert_true(self.test_news_published(
            len(json_resp['data']['list']), json_resp))
        tools.assert_equals(json_resp['data']['page_sum'], length//20+1)
        tools.assert_equals(json_resp['data']['current_page'], 1)

        response = test_app.get(f'api/v1/news?day={day_str}&page=2',
                                headers=headers)
        json_resp = self.validate_response(response)
        tools.assert_true(self.test_news_published(
            len(json_resp['data']['list']), json_resp))
        tools.assert_equals(json_resp['data']['page_sum'], length//20+1)
        tools.assert_equals(json_resp['data']['current_page'], 2)

    @tools.nottest
    def test_search(self, article_group, count):
        """
        测试搜索功能

        @param article_group: 文章所在的group(edited或者news)
        @tpye search_word: str
        @param count: 状态为published文章的数量
        @tpye count: int
        @return: None
        @rtype: None
        """
        self.change_user_level(9)
        headers = {'Authorization': self.token}
        url = f'/api/v1/{article_group}?search=a'
        response = test_app.get(url, headers=headers)
        json_resp = self.validate_response(response)
        tools.assert_equals(json_resp['data']['count'], 0)

        url = f'/api/v1/{article_group}?search=s'
        response = test_app.get(url, headers=headers)
        json_resp = self.validate_response(response)
        tools.assert_equals(json_resp['data']['count'], count)

        url = f'/api/v1/{article_group}?state=published&search=s'
        response = test_app.get(url, headers=headers)
        json_resp = self.validate_response(response)
        tools.assert_equals(json_resp['data']['count'], count)

        edited_articles = EditedArticle.objects().limit(3)
        for edited_article in edited_articles:
            edited_article.state = 'edited'
            edited_article.save()
        url = f'/api/v1/{article_group}?state=published&search=s'
        response = test_app.get(url, headers=headers)
        json_resp = self.validate_response(response)
        tools.assert_equals(json_resp['data']['count'], count - 3)

        edited_articles = EditedArticle.objects().limit(3)
        for edited_article in edited_articles:
            edited_article.state = 'published'
            edited_article.save()

    def test_edited_article_api(self):
        """
        测试edited_article的get接口，发送请求情况

        1、测试登录认证
        2、测试改变order_by，验证查询结果
        3、测试查询结果的分页功能及按状态查询
        4、测试查询详情
        """
        headers = {'Authorization': self.token}
        response = test_app.get('/api/v1/edited',
                                headers=headers)
        json_resp = self.validate_response(response, 200)
        length = EditedArticle.objects(state='published').count()
        tools.assert_equals(len(json_resp['data']['list']), 20)
        tools.assert_equals(json_resp['data']['count'], length)
        tools.assert_equals(json_resp['data']['page_sum'], length//20+1)
        tools.assert_equals(json_resp['data']['current_page'], 1)
        tools.assert_equals(json_resp['data']['list'][0].get(
            'id'), str(self.edited_id_list[-1]))
        item = EditedArticle.get_by_id(self.edited_id_list[-1])
        tools.assert_equals(
            json_resp['data']['list'][0], item.api_base_response())

        headers = {'Authorization': self.token}
        response = test_app.get('/api/v1/edited?order_by=added',
                                headers=headers)
        json_resp = self.validate_response(response)
        tools.assert_not_equals(json_resp['data']['list'][0],
                                EditedArticle.get_by_id
                                (self.edited_id_list[-1]).api_base_response())
        tools.assert_equals(json_resp['data']['list'][0],
                            EditedArticle.get_by_id(self.edited_id_list[0]).
                            api_base_response())

        url = '/api/v1/edited?page=2&page_size=20&state=published'
        response = test_app.get(url, headers=headers)
        json_resp = self.validate_response(response, 200)
        length = EditedArticle.objects(state='published').count()
        tools.assert_equals(len(json_resp['data']['list']), length-20)
        tools.assert_equals(json_resp['data']['count'], length)
        tools.assert_equals(json_resp['data']['page_sum'], length//20+1)
        tools.assert_equals(json_resp['data']['current_page'], 2)

        url = '/api/v1/edited?state=all'
        response = test_app.get(url, headers=headers)
        json_resp = self.validate_response(response, 200)
        length = EditedArticle.objects().count()
        tools.assert_equals(len(json_resp['data']['list']), 20)
        tools.assert_equals(json_resp['data']['count'], length)
        tools.assert_equals(json_resp['data']['page_sum'], length//20+1)
        tools.assert_equals(json_resp['data']['current_page'], 1)

        test_article = EditedArticle.get_by_id(self.edited_id_list[1])
        url = f'/api/v1/edited/{str(self.edited_id_list[1])}'
        response = test_app.get(url, headers=headers)
        json_resp = self.validate_response(response, 200)
        tools.assert_is_not_none(json_resp['data'])
        tools.assert_equals(json_resp['data'], test_article.api_response())
        edited_count = EditedArticle.objects(state='published').count()
        self.test_search('edited', edited_count)

    def test_edited_article_post(self):
        """
        测试edited_article的post接口

        1、测试传错误或者不传token能否修改文章
        2、测试登录认证
        3、测试权限，普通用户不能新增
        4、不传raw_article新增，article_from为1
        5、传raw_article新增，article_from为0
        4、不传时间新增
        """
        api_url = 'api/v1/edited'
        api_method = test_app.post
        self.test_api_jwt(api_url, api_method)

        headers = {'Authorization': self.token}
        self.change_user_level(1)
        response = test_app.post('/api/v1/edited',
                                 data=json.dumps(self.edited_data),
                                 headers=headers,
                                 content_type='application/json')
        json_resp = self.validate_response(response, 500)
        tools.assert_equals(json_resp.get("data"),
                            {'msg': "user don't has authority"})

        self.change_user_level(9)
        data = deepcopy(self.edited_data)
        data['state'] = 'edited'
        data['published'] = datetime.now().timestamp()
        response = test_app.post('/api/v1/edited',
                                 data=json.dumps(data),
                                 headers=headers,
                                 content_type='application/json')
        json_resp = self.validate_response(response, 200)
        tools.assert_is_not_none(json_resp.get('data'))
        tools.assert_is_not_none(json_resp.get('data').get('id'))
        tools.assert_equals(json_resp.get('data').get('article_from'), 1)

        data = deepcopy(self.edited_data)
        data['state'] = 'edited'
        data['published'] = datetime.now().timestamp() + 10000
        data['added'] = datetime.now().timestamp() - 1000
        data['date'] = datetime.now().timestamp() - 2000
        data['updated'] = datetime.now().timestamp() - 2000
        data['url'] = 'http://www.sohu.com'
        data['raw_article'] = str(self.raw_id)
        response = test_app.post('/api/v1/edited',
                                 data=json.dumps(data),
                                 headers=headers,
                                 content_type='application/json')
        json_resp = self.validate_response(response, 200).get('data')
        tools.assert_is_not_none(json_resp.get('id'))
        tools.assert_not_equals(json_resp.get('published'), data['published'])
        tools.assert_not_equals(json_resp.get('added'), data['added'])
        tools.assert_not_equals(json_resp.get('date'), data['date'])
        tools.assert_not_equals(json_resp.get('updated'), data['updated'])
        tools.assert_equals(json_resp.get('article_from'), 0)
        tools.assert_equals(json_resp.get('raw_article'), str(self.raw_id))
        article = RawArticle.get_by_id(str(self.raw_id))
        tools.assert_equals(article.is_edited, True)

        data.pop('added')
        data.pop('date')
        data['url'] = 'http://www.sohu'
        response = test_app.post('/api/v1/edited',
                                 data=json.dumps(data),
                                 headers=headers,
                                 content_type='application/json')
        json_resp = self.validate_response(response).get('data')
        tools.assert_is_not_none(json_resp.get('added'))
        tools.assert_is_not_none(json_resp.get('date'))
        tools.assert_equals(json_resp.get('cn_title'),
                            data['cn_title'])
        tools.assert_equals(json_resp.get('cn_content'),
                            data['cn_content'])
        tools.assert_equals(json_resp.get('state'),
                            data['state'])
        EditedArticle.objects(state='edited').delete()

    def test_put_edited_article(self):
        """
        测试edited_article的put接口

        1、测试传错误或者不传token能否修改文章
        2、测试登录认证
        3、测试修改权限
        4、不传时间修改
        """
        api_url = 'api/v1/edited'
        api_method = test_app.put
        self.test_api_jwt(api_url, api_method)

        headers = {'Authorization': self.token}
        data = deepcopy(self.edited_data)
        data['cn_title'] = '测试111'
        data['state'] = 'pending'
        data['cn_summary'] = '测试aaa'
        data['published'] = datetime.now().timestamp() + 1000
        data['added'] = datetime.now().timestamp() - 1000
        data['date'] = datetime.now().timestamp() - 1000
        data['updated'] = datetime.now().timestamp() - 1000
        response = test_app.put('/api/v1/edited',
                                headers=headers,
                                data=json.dumps(data),
                                content_type='application/json')
        self.validate_response(response, 400)

        self.change_user_level(1)
        response = test_app.put(
            f'api/v1/edited/{str(self.edited_id_list[1])}',
            data=json.dumps(data),
            headers=headers,
            content_type='application/json')
        self.validate_response(response, 500)

        self.change_user_level(9)
        response = test_app.put(
            f'api/v1/edited/{str(self.edited_id_list[1])}',
            data=json.dumps(data),
            headers=headers,
            content_type='application/json')
        json_resp = self.validate_response(response, 200)
        tools.assert_equals(json_resp['data']['cn_title'],
                            data['cn_title'])
        tools.assert_equals(json_resp['data']['state'],
                            data['state'])
        tools.assert_equals(json_resp['data']['cn_summary'],
                            data['cn_summary'])

        data.pop('added')
        data.pop('date')
        data.pop('published')
        response = test_app.put(
            f'/api/v1/edited/{str(self.edited_id_list[1])}',
            data=json.dumps(data),
            headers=headers,
            content_type='application/json')
        json_resp = json.loads(response.data).get('data')
        tools.assert_is_not_none(json_resp.get('added'))
        tools.assert_is_not_none(json_resp.get('date'))
        tools.assert_is_not_none(json_resp.get('published'))

        response = test_app.get(
            f'/api/v1/edited/{str(self.edited_id_list[1])}',
            headers=headers)
        json_resp = self.validate_response(response, 200)
        tools.assert_not_equals(json_resp.get('cn_title'),
                                data['cn_title'])
        tools.assert_not_equals(json_resp.get('cn_content'),
                                data['cn_content'])
        tools.assert_not_equals(json_resp.get('state'),
                                data['state'])

    def test_zdelete_edited_article(self):
        """
        测试edited_article的delete接口
        """
        api_url = 'api/v1/edited'
        api_method = test_app.delete
        self.test_api_jwt(api_url, api_method)
        
        amount = EditedArticle.objects().count()
        cache_id = self.edited_id_list[1]

        # print(type(EditedArticle.objects(id=cache_id)))
        # print(type(EditedArticle.objects(id=cache_id).first()))
        headers = {'Authorization': self.token}
        response = test_app.delete(
            f'/api/v1/edited/{str(self.edited_id_list[1])}',
            headers=headers
            )
        json_resp = self.validate_response(response, 200)
        # print(EditedArticle.objects().count())
        tools.assert_equals(json_resp.get('data'), {'msg': 'edited_article deleted.'})
        tools.assert_is_none(EditedArticle.objects(id=cache_id).first())
        tools.assert_equals(amount-1, EditedArticle.objects().count())


    def test_holoread_article_get(self):
        """
        测试holoread_article的get接口

        1、测试published排序
        2、测试查询参数last及count
        """
        api_url = 'api/v1/articles'
        count = 10
        response = test_app.get(f'{api_url}?count={count}')
        json_resp = self.validate_response(response, 200)
        data = json_resp.get('data')
        tools.assert_equals(count, len(data))
        tools.assert_equals(str(self.edited_id_list[0]),
                            data[0]['_id'])

        last = int(time.time() + 100)
        response = test_app.get(f'{api_url}?last={last}')
        json_resp = self.validate_response(response, 200)
        data = json_resp.get('data')
        tools.assert_equals(0, len(data))

        articles = EditedArticle.objects().limit(3)
        for article in articles:
            article.state = 'pending'
            article.save()
        response = test_app.get(f'{api_url}')
        json_resp = self.validate_response(response, 200)
        data = json_resp.get('data')
        tools.assert_equals(len(data),
                            len(self.edited_id_list) - 3)
        for article in articles:
            article.state = 'published'
            article.save()
