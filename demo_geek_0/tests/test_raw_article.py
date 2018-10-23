from nose import tools
from datetime import datetime

import json
from copy import deepcopy

from tests import test_app, BaseTest, article_data, user_data
from geek_digest.model import RawArticle
from geek_digest.common.constant import RawArticleConstant

news = [{'title': '中兴终端CEO程立新离职', 'source': 'cnbeta', 'source_cn': 'cnBeta',
         'url': 'http://www.cnbeta.com/articles/tech/744077.htm',
         'date': 1530949320}]


class TestRawArticle(BaseTest):
    @classmethod
    def setup_class(cls):
        cls.user_data = deepcopy(user_data)
        cls.article_data = deepcopy(article_data)
        cls.raw_id_list = []
        cls.test_login()
        cls.__test_save_raw_article()

    @classmethod
    def teardown_class(cls):
        cls.clean_user()
        for id in cls.raw_id_list:
            raw_article = RawArticle.objects(id=id).first()
            if raw_article:
                raw_article.delete()

    @classmethod
    def __test_save_raw_article(cls):
        for i in range(25):
            raw_article = RawArticle(**cls.article_data)
            raw_article.url = raw_article.url + str(i)
            raw_article.save()
            cls.raw_id_list.append(raw_article.id)

    @tools.nottest
    def test_paging(self, response, query, page, page_size=20):
        """
        翻页功能测试

        @param page: 页数
        @type page: int
        @param page_size: 每页条数
        @type page_size: int
        @param query: 查询条件
        @type querya: dict
        @return: None
        @rtype: None
        """
        tools.assert_equals(response.status_code, 200)
        json_resp = json.loads(response.data)
        article = RawArticle.objects(**query)
        length = len(article)
        list_len = page_size

        tools.assert_equals(json_resp['data']['page_sum'], length//20+1)
        if page == json_resp['data']['page_sum']:
            list_len = length % page_size
            if list_len == 0:
                list_len = 20

        tools.assert_equals(len(json_resp['data']['list']), list_len)

        tools.assert_equals(json_resp['data']['count'], length)
        tools.assert_equals(json_resp['data']['current_page'], page)

        if page == 1:
            tools.assert_equals(json_resp['data']['list'][0].get(
                'id'), str(self.raw_id_list[-1]))
            tools.assert_is_not_none(json_resp['data']['list'][0].get('news'))
            tools.assert_is_not_none(
                json_resp['data']['list'][0].get('news_count'))

    @tools.nottest
    def test_search(self, search_word):
        """
        输入搜索关键字，测试文章能否被检出

        @param search_word: 输入的搜索关键字
        @tpye search_word: str
        @return: None
        @rtype: None
        """
        self.change_user_level(9)
        headers = {'Authorization': self.token}
        url = f'/api/v1/raw_article?search={search_word}'
        response = test_app.get(url, headers=headers)
        query = {
            'is_edited': False,
            'is_translated': True
        }
        self.test_paging(response, query, 1)

        url = f'/api/v1/raw_article?search={search_word}&page=2'
        response = test_app.get(url, headers=headers)
        self.test_paging(response, query, 2)

        url = '/api/v1/raw_article?search=a'
        response = test_app.get(url, headers=headers)
        json_resp = self.validate_response(response)
        tools.assert_equals(json_resp['data']['count'], 0)

        if search_word != '测':
            self.test_search('测')

    def test_language(self):
        """
        测试查询不同语言的文章

        1、测试传入错误的语言格式查询
        2、测试查询英文文章，未存，返回值为0
        3、测试查询中文文章，检查返回值是否正确
        4、测试查询结果是否按照入库时间倒序
        5、测试查询结果的翻页功能
        """
        self.change_user_level(9)
        headers = {'Authorization': self.token}
        response = test_app.get('/api/v1/raw_article?language=CN',
                                headers=headers)
        json_resp = self.validate_response(response)
        tools.assert_equals(json_resp['data']['count'], 0)

        headers = {'Authorization': self.token}
        response = test_app.get('/api/v1/raw_article?language=en',
                                headers=headers)
        json_resp = self.validate_response(response)
        tools.assert_equals(json_resp['data']['count'], 0)

        headers = {'Authorization': self.token}
        response = test_app.get('/api/v1/raw_article?language=cn',
                                headers=headers)
        json_resp = self.validate_response(response)
        query = {
            'is_edited': False,
            'is_translated': True,
            'language': RawArticleConstant.LANGUAGE_CN
        }
        self.test_paging(response, query, 1)
        tools.assert_equals(json_resp['data']['count'], 25)
        tools.assert_not_equals(json_resp['data']['list'][0],
                                RawArticle.get_by_id(self.raw_id_list[0]).
                                api_base_response())
        tools.assert_equals(json_resp['data']['list'][0],
                            RawArticle.get_by_id(self.raw_id_list[-1]).
                            api_base_response())

        headers = {'Authorization': self.token}
        response = test_app.get('/api/v1/raw_article?language=cn&page=2',
                                headers=headers)
        json_resp = self.validate_response(response)
        self.test_paging(response, query, 2)

    def test_is_cluster(self):
        """
        测试查看聚类文章

        1、测试查询聚类文章，返回值为0
        2、测试is_cluster不为Ture时是否默认查全部
        3、测试查询结果是否按照入库时间倒序
        4、测试查询结果的翻页功能
        """
        self.change_user_level(9)
        headers = {'Authorization': self.token}
        response = test_app.get('/api/v1/raw_article?is_cluster=true',
                                headers=headers)
        json_resp = self.validate_response(response)
        tools.assert_equals(json_resp['data']['count'], 0)

        headers = {'Authorization': self.token}
        response = test_app.get('/api/v1/raw_article?is_cluster=',
                                headers=headers)
        json_resp = self.validate_response(response)
        query = {
            'is_edited': False,
            'is_translated': True
        }
        self.test_paging(response, query, 1)
        tools.assert_equals(json_resp['data']['count'], 25)
        tools.assert_not_equals(json_resp['data']['list'][0],
                                RawArticle.get_by_id(self.raw_id_list[0]).
                                api_base_response())
        tools.assert_equals(json_resp['data']['list'][0],
                            RawArticle.get_by_id(self.raw_id_list[-1]).
                            api_base_response())

        headers = {'Authorization': self.token}
        response = test_app.get('/api/v1/raw_article?is_cluster&page=2',
                                headers=headers)
        self.validate_response(response)
        self.test_paging(response, query, 2)

        raw_article = RawArticle.objects().limit(3)
        for article in raw_article:
            article.news_count = 5
            article.save()

        headers = {'Authorization': self.token}
        response = test_app.get('/api/v1/raw_article?is_cluster=true',
                                headers=headers)
        json_resp = self.validate_response(response)
        tools.assert_equals(json_resp['data']['count'], 3)
        tools.assert_equals(json_resp['data']['list'][0],
                            RawArticle.get_by_id(self.raw_id_list[2]).
                            api_base_response())
        tools.assert_not_equals(json_resp['data']['list'][0],
                                RawArticle.get_by_id(self.raw_id_list[0]).
                                api_base_response())

    def test_day(self):
        """
        测试传入日期，查询某天文章

        1、测试传入没有文章的一天，返回值为0
        2、测试传入正确时间，检查返回值
        3、测试查询结果是否按照入库时间倒序
        4、测试查询结果的翻页功能
        """
        __time = datetime.now()
        day_str = __time.strftime('%Y%m%d')
        self.change_user_level(9)
        headers = {'Authorization': self.token}
        response = test_app.get('/api/v1/raw_article?day=20100101',
                                headers=headers)
        json_resp = self.validate_response(response)
        tools.assert_equals(json_resp['data']['count'], 0)

        response = test_app.get(f'api/v1/raw_article?day={day_str}',
                                headers=headers)
        json_resp = self.validate_response(response)
        query = {
            'is_edited': False,
            'is_translated': True
        }
        self.test_paging(response, query, 1)
        tools.assert_equals(json_resp['data']['count'], 25)
        tools.assert_not_equals(json_resp['data']['list'][0],
                                RawArticle.get_by_id(self.raw_id_list[1]).
                                api_base_response())
        tools.assert_equals(json_resp['data']['list'][0],
                            RawArticle.get_by_id(self.raw_id_list[-1]).
                            api_base_response())

        response = test_app.get(f'api/v1/raw_article?day={day_str}&page=2',
                                headers=headers)
        json_resp = self.validate_response(response)
        self.test_paging(response, query, 2)

    def test_raw_article_get_api(self):
        """
        测试raw_article的get接口，发送请求情况
        1、测试请求成功
        2、测试分页功能
        3、测试不加token认证
        4、测试token值
        5、测试查询详情
        6、测试用户权限
        7、测试搜索功能
        """
        # 测试请求成功 & 测试分页功能(page=1)
        self.change_user_level()
        headers = {'Authorization': self.token}
        response = test_app.get('/api/v1/raw_article', headers=headers)
        query = {
            'is_edited': False,
            'is_translated': True,
            'language': RawArticleConstant.LANGUAGE_CN
        }
        self.test_paging(response, query, 1)

        # 测试请求成功 & 测试分页功能(page=2)
        headers = {'Authorization': self.token}
        response = test_app.get('/api/v1/raw_article?page=2&page_size=20',
                                headers=headers)
        self.test_paging(response, query, 2)

        # 测试请求所有文章成功 & 测试分页功能(page=1)
        headers = {'Authorization': self.token}
        response = test_app.get('/api/v1/raw_article', headers=headers)
        query = {
            'is_edited': False,
            'is_translated': True
        }
        self.test_paging(response, query, 1)

        # 测试请求所有文章成功 & 测试分页功能(page=2)
        headers = {'Authorization': self.token}
        response = test_app.get('/api/v1/raw_article?page=2&page_size=20',
                                headers=headers)
        self.test_paging(response, query, 2)

        # 测试不加token认证 & 测试错误的token值
        self.test_api_jwt('/api/v1/user/raw_article', test_app.get)

        # 测试order_by
        headers = {'Authorization': self.token}
        response = test_app.get('/api/v1/raw_article?order_by=added',
                                headers=headers)
        json_resp = self.validate_response(response, 200)
        tools.assert_not_equals(json_resp['data']['list'][0],
                                RawArticle.get_by_id(self.raw_id_list[-1]).
                                api_base_response())
        tools.assert_equals(json_resp['data']['list'][0],
                            RawArticle.get_by_id(self.raw_id_list[0]).
                            api_base_response())

        # 测试传入多个值
        headers = {'Authorization': self.token}
        response = test_app.get(
            '/api/v1/raw_article?order_by=-added&order_by=-news_count',
            headers=headers)
        self.validate_response(response, 200)
        tools.assert_equals(json_resp['data']['list'][0]['news_count'], 5)
        tools.assert_equals(json_resp['data']['list'][1]['news_count'], 5)
        tools.assert_equals(json_resp['data']['list'][2]['news_count'], 5)
        tools.assert_not_equals(json_resp['data']['list'][3]['news_count'], 5)

        # 测试查询详情
        headers = {'Authorization': self.token}
        test_article = RawArticle.get_by_id(self.raw_id_list[1])
        response = test_app.get(
            f'/api/v1/raw_article/{str(self.raw_id_list[1])}',
            headers=headers)
        json_resp = self.validate_response(response)

        tools.assert_is_not_none(json_resp['data'])
        tools.assert_equals(json_resp['data'], test_article.api_response())
        tools.assert_is_not_none(json_resp['data'].get('news'))
        tools.assert_is_not_none(json_resp['data'].get('news_count'))
        tools.assert_equals(json_resp['data'].get('cn_title'),
                            RawArticle.objects()[1].cn_title)
        tools.assert_equals(json_resp['data'].get('cn_content'),
                            RawArticle.objects()[1].cn_content)
        tools.assert_equals(json_resp['data'].get('url'),
                            RawArticle.objects()[1].url)

        # 测试搜索功能
        headers = {'Authorization': self.token}

        # 测试用户权限
        self.change_user_level(1)
        headers = {'Authorization': self.token}
        test_article = RawArticle.get_by_id(self.raw_id_list[1])
        response = test_app.get(
            f'/api/v1/raw_article/{str(self.raw_id_list[1])}',
            headers=headers)
        json_resp = json.loads(response.data)
        tools.assert_equals(response.status_code, 500)
        tools.assert_equals(json.loads(response.data)['data'],
                            {'msg': "user don't has authority"})

        self.test_search('一')
        self.delete_articles()
