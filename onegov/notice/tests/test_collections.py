from onegov.notice import OfficialNoticeCollection
from transaction import commit


def test_notice_collection(session):
    notices = OfficialNoticeCollection(session)
    assert notices.query().count() == 0

    notice_1 = notices.add(
        title='Important Announcement',
        text='<em>Important</em> things happened!',
        category='important'
    )
    notice_1.submit()
    notice_1.publish()

    commit()

    notice_1 = notices.query().one()
    assert notice_1.title == 'Important Announcement'
    assert notice_1.text == '<em>Important</em> things happened!'
    assert notice_1.category == 'important'

    notice_2 = notices.add(
        title='Important Announcement',
        text='<em>Important</em> things happened!'
    )
    notice_2.submit()

    assert notices.query().count() == 2
    assert notices.for_state('drafted').query().count() == 0
    assert notices.for_state('submitted').query().count() == 1
    assert notices.for_state('published').query().count() == 1

    assert notices.by_name('important-announcement')
    assert notices.by_name('important-announcement-1')

    assert notices.by_id(notice_1.id)
    assert notices.by_id(notice_2.id)

    notices.delete(notice_1)
    notices.delete(notice_2)

    assert notices.query().count() == 0
    assert notices.for_state('drafted').query().count() == 0
    assert notices.for_state('submitted').query().count() == 0
    assert notices.for_state('published').query().count() == 0


def test_notice_collection_search(session):
    notices = OfficialNoticeCollection(session)
    for title, text, state in (
        ('First', 'Lorem Ipsum', 'drafted'),
        ('Second', 'A text', 'submitted'),
        ('Third', 'Anöther text', 'drafted'),
        ('Fourth', 'A fourth text', 'published'),
        ('Fifth', 'Lorem Ipsum', 'rejected'),
        ('Sixt', '<p>Six</p>', 'published'),
        ('Sübent', 'Sübent', 'drafted'),
    ):
        notice = notices.add(title=title, text=text)
        notice.state = state

    assert notices.query().count() == 7

    notices.term = 'Third'
    assert notices.query().count() == 1

    notices.term = 'ourth'
    assert notices.query().count() == 1

    notices.term = 'ipsum'
    assert notices.query().count() == 2
    assert notices.for_state('rejected').query().count() == 1

    notices.term = 'six'
    assert notices.query().count() == 1
    assert notices.for_state('rejected').query().count() == 0

    notices.term = 'üb'
    assert notices.query().count() == 1


def test_notice_collection_pagination(session):
    notices = OfficialNoticeCollection(session)

    assert notices.page_index == 0
    assert notices.pages_count == 0
    assert notices.batch == []

    for year in range(2008, 2010):
        for month in range(1, 13):
            notice = notices.add(
                title='Notice {0}-{1}'.format(year, month),
                text='A' if month % 3 else 'B'
            )
            notice.submit()
            if year > 2008:
                notice.publish()
    assert notices.query().count() == 24

    assert notices.for_state('drafted').subset_count == 0

    submitted = notices.for_state('submitted')
    assert submitted.subset_count == 12
    assert len(submitted.next.batch) == 12 - submitted.batch_size

    published = notices.for_state('published')
    assert published.subset_count == 12
    assert len(published.next.batch) == 12 - published.batch_size

    published.term = 'A'
    assert published.subset_count == 12
    assert len(published.next.batch) == 0
