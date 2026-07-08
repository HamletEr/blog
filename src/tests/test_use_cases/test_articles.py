import pytest

from blog_app.domain.entities.articles import Article, ArticleData
from blog_app.domain.entities.users import User
from blog_app.domain.exceptions.articles import ArticleNotFoundError, PermissionDenied, TooShortText
from blog_app.domain.exceptions.users import AuthenticationRequired
from blog_app.use_cases.articles import (
    CreateArticleData,
    DeleteArticleData,
    GetArticleById,
    GetListArticles,
    UpdateArticleData,
)


async def test_anonymous_user_cannot_create_article(repository_fixture, article_data_factory):
    article_data: ArticleData = article_data_factory()

    with pytest.raises(AuthenticationRequired):
        await CreateArticleData(repo=repository_fixture, user=None).execute(article_data)


async def test_common_user_create_article(repository_fixture, user_factory, article_data_factory):
    common_user: User = user_factory(is_admin=False)
    article_data: ArticleData = article_data_factory()

    with pytest.raises(PermissionDenied):
        await CreateArticleData(repo=repository_fixture, user=common_user).execute(article_data)


async def test_admin_user_create_article(repository_fixture, user_factory, article_data_factory):
    admin_user: User = user_factory(is_admin=True)
    article_data: ArticleData = article_data_factory()
    short_title_data: ArticleData = article_data_factory(title='st')
    short_content_data: ArticleData = article_data_factory(content='sc')
    article = await CreateArticleData(repo=repository_fixture, user=admin_user).execute(article_data)
    article_id = article.id

    article_in_repo = await GetArticleById(repo=repository_fixture, user=admin_user).execute(article_id)

    with pytest.raises(TooShortText):
        await CreateArticleData(repo=repository_fixture, user=admin_user).execute(short_title_data)

    with pytest.raises(TooShortText):
        await CreateArticleData(repo=repository_fixture, user=admin_user).execute(short_content_data)

    assert article_data == article_in_repo.data
    assert article_id == article_in_repo.id
    assert len(await GetListArticles(repo=repository_fixture, user=admin_user).execute()) == 1


async def test_common_user_update_article(repository_fixture, user_factory, article_data_factory):
    admin_user: User = user_factory(is_admin=True)
    common_user: User = user_factory(is_admin=False)
    article_data: ArticleData = article_data_factory()
    article = await CreateArticleData(repo=repository_fixture, user=admin_user).execute(article_data)
    article_id = article.id

    with pytest.raises(PermissionDenied):
        await UpdateArticleData(repo=repository_fixture, user=common_user).execute(article_id, article_data)


async def test_admin_user_update_article(repository_fixture, user_factory, article_data_factory):
    admin_user: User = user_factory(is_admin=True)
    article_data: ArticleData = article_data_factory()
    article = await CreateArticleData(repo=repository_fixture, user=admin_user).execute(article_data)
    article_id = article.id
    new_article_data = article_data_factory(title='updated_title', content='updated_content')

    updated_article = await (UpdateArticleData(repo=repository_fixture, user=admin_user)
                             .execute(article_id, new_article_data))

    assert new_article_data == updated_article.data
    assert article.id == updated_article.id


async def test_common_user_delete_article(repository_fixture, user_factory, article_data_factory):
    admin_user: User = user_factory(is_admin=True)
    common_user: User = user_factory(is_admin=False)
    article_data: ArticleData = article_data_factory()
    article = await CreateArticleData(repo=repository_fixture, user=admin_user).execute(article_data)
    article_id = article.id

    with pytest.raises(PermissionDenied):
        await DeleteArticleData(repo=repository_fixture, user=common_user).execute(article_id)


async def test_admin_user_delete_article(repository_fixture, user_factory, article_data_factory):
    admin_user: User = user_factory(is_admin=True)
    article_data: ArticleData = article_data_factory()
    article = await CreateArticleData(repo=repository_fixture, user=admin_user).execute(article_data)
    article_id = article.id

    await DeleteArticleData(repo=repository_fixture, user=admin_user).execute(article_id)

    with pytest.raises(ArticleNotFoundError):
        await GetArticleById(repo=repository_fixture, user=admin_user).execute(article_id)

    assert len(await GetListArticles(repo=repository_fixture, user=admin_user).execute()) == 0


async def test_get_article_by_id(repository_fixture, user_factory, article_data_factory):
    admin_user: User = user_factory(is_admin=True)
    common_user: User = user_factory(is_admin=False)
    article_data: ArticleData = article_data_factory()
    article = await CreateArticleData(repo=repository_fixture, user=admin_user).execute(article_data)

    article_looking_for = await GetArticleById(repo=repository_fixture, user=common_user).execute(article.id)

    assert isinstance(article_looking_for, Article)
    assert article.id == article_looking_for.id


async def test_get_list_articles(repository_fixture, user_factory, article_data_factory):
    admin_user: User = user_factory(is_admin=True)
    common_user: User = user_factory(is_admin=False)
    articles_count = 3
    for i in range(articles_count):
        await (
            CreateArticleData(repository_fixture, user=admin_user)
            .execute(article_data_factory(
                title=f"test_title{i}",
                content=f"test_content{i}"
            )))

    result_list = await GetListArticles(repo=repository_fixture, user=common_user).execute()

    assert len(result_list) == articles_count
    assert all(isinstance(article, Article) for article in result_list)


async def test_get_list_by_text(repository_fixture, user_factory, article_data_factory):
    admin_user: User = user_factory(is_admin=True)
    common_user: User = user_factory(is_admin=False)
    articles_count = 3
    for i in range(articles_count):
        await (
            CreateArticleData(repository_fixture, user=admin_user)
            .execute(article_data_factory(
                title=f"test_title{i}",
                content=f"test_content{i}"
            )))

    with pytest.raises(TooShortText):
        await GetListArticles(repo=repository_fixture, user=common_user).execute(looking_text='te')

    result_list = await GetListArticles(repo=repository_fixture, user=common_user).execute(looking_text='title1')

    assert len(result_list) == 1
