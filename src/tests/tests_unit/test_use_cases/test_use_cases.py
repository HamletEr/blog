from unittest.mock import Mock, AsyncMock
from uuid import uuid4

import pytest

from blog_app.domain.entities.users import User
from blog_app.domain.entities.articles import ArticleData, Article
from blog_app.domain.exceptions.articles import ArticleNotFoundError, TooShortText, PermissionDenied
from blog_app.domain.exceptions.users import AuthenticationRequired
from blog_app.domain.repositories.articles import ArticleRepository
from blog_app.use_cases.articles import (
    CreateArticle,
    DeleteArticle,
    GetArticleById,
    GetListArticles,
    UpdateArticle,
)


async def test_anonymous_user_cannot_create_article():
    repo = AsyncMock(ArticleRepository)
    article_data = Mock(ArticleData)

    with pytest.raises(AuthenticationRequired):
        await CreateArticle(repo=repo, user=None).execute(article_data)


async def test_get_article_by_id():
    repo = AsyncMock(ArticleRepository)
    user = Mock(User)
    article = Mock(Article)

    repo.get_by_id.return_value = None

    with pytest.raises(ArticleNotFoundError):
        await GetArticleById(repo=repo, user=user).execute(uuid4())

    repo.get_by_id.return_value = article

    assert await GetArticleById(repo=repo, user=user).execute(uuid4()) == article


async def test_get_list_articles():
    repo = AsyncMock(ArticleRepository)
    user = Mock(User)
    res_list = [Mock(Article), Mock(Article)]
    repo.get_list.return_value = res_list

    with pytest.raises(TooShortText):
        await GetListArticles(repo=repo, user=user).execute(looking_text='a')
    assert await GetListArticles(repo=repo, user=user).execute(limit_on_page=2, page=1) == res_list


async def test_create_article():
    repo = AsyncMock(ArticleRepository)
    user = Mock(User)
    user.is_admin = True
    article_data = Mock(ArticleData)
    article_data.title = 'Test Title'
    article_data.content = 't'
    res_article = Mock(Article)
    repo.create.return_value = res_article

    with pytest.raises(TooShortText):
        await CreateArticle(repo=repo, user=user).execute(article_data)

    article_data.content = 'Test Content'
    assert await CreateArticle(repo=repo, user=user).execute(article_data) == res_article


async def test_update_article():
    repo = AsyncMock(ArticleRepository)
    user = Mock(User)
    article_data = Mock(ArticleData)
    article_data.title = 'Test Title'
    article_data.content = 'Test Content'
    result_article = Mock(Article)
    repo.update.return_value = result_article

    user.is_admin = False
    with pytest.raises(PermissionDenied):
        await UpdateArticle(repo=repo, user=user).execute(uuid4(), article_data)

    user.is_admin = True
    assert await UpdateArticle(repo=repo, user=user).execute(uuid4(), article_data) == result_article


async def test_delete_article():
    repo = AsyncMock(ArticleRepository)
    user = Mock(User)
    user.is_admin = True
    repo.delete.return_value = None

    assert await DeleteArticle(repo=repo, user=user).execute(uuid4()) is None
