from datetime import datetime, UTC
from uuid import uuid4

import pytest

from blog_app.domain.entities.articles import Article, ArticleData
from blog_app.infrastructure.models.articles import ArticleModel


@pytest.fixture
def article_model_factory():
    def _create_article(
        id=uuid4(),
        is_active=True,
        title='Title',
        content='Content',
        category_id=1,
        image_url='https://example.com/img1.jpg',
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    ):
        return ArticleModel(
            id=id,
            is_active=is_active,
            title=title,
            content=content,
            category_id=category_id,
            image_url=image_url,
            created_at=created_at,
            updated_at=updated_at,
        )
    return _create_article


@pytest.fixture
def article_domain_factory():
    def _create_article(
        id=uuid4(),
        is_active=True,
        title='Title',
        content='Content',
        category_id=1,
        image_url='https://example.com/img1.jpg',
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    ):
        return Article(
            id=id,
            is_active=is_active,
            data=ArticleData(
                title=title,
                content=content,
                category_id=category_id,
                image_url=image_url,
            ),
            created_at=created_at,
            updated_at=updated_at,
        )
    return _create_article
