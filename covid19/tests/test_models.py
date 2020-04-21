import shutil
from datetime import date, timedelta
from model_bakery import baker
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase

from covid19.models import StateSpreadsheet
from covid19.signals import new_spreadsheet_imported_signal


class StateSpreadsheetTests(TestCase):

    def tearDown(self):
        if Path(settings.MEDIA_ROOT).exists():
            shutil.rmtree(settings.MEDIA_ROOT)

    def test_format_filename_to_add_uf_date_username(self):
        today = date.today()

        spreadsheet = baker.make(
            StateSpreadsheet,
            user__username='foo',
            state='rj',
            date=today,
            _create_files=True,  # will create a dummy .txt file
        )
        expected = f'{settings.MEDIA_ROOT}/covid19/rj/casos-rj-{today.isoformat()}-foo-1.txt'

        assert expected == spreadsheet.file.path

    def test_format_filename_counting_previous_uploads_from_user(self):
        today = date.today()
        user = baker.make(settings.AUTH_USER_MODEL, username='foo')
        state = 'rj'
        prev_qtd = 4
        baker.make(
            StateSpreadsheet,
            user=user,
            state=state,
            date=today,
            _quantity=prev_qtd
        )
        baker.make(  # other state, same date
            StateSpreadsheet,
            user=user,
            state='sp',
            date=today,
        )
        baker.make(  # other date, same state
            StateSpreadsheet,
            user=user,
            state=state,
            date=today + timedelta(days=1),
        )
        baker.make(  # same date, same state, other user
            StateSpreadsheet,
            user__username='new_user',
            state=state,
            date=today,
        )

        spreadsheet = baker.make(
            StateSpreadsheet,
            user=user,
            state=state,
            date=today,
            _create_files=True
        )
        expected = f'{settings.MEDIA_ROOT}/covid19/rj/casos-rj-{today.isoformat()}-foo-5.txt'

        assert expected == spreadsheet.file.path

    def test_filter_older_versions_exclude_the_object_if_id(self):
        kwargs = {
            'date': date.today(), 'user': baker.make(settings.AUTH_USER_MODEL), 'state': 'rj',
        }
        baker.make(StateSpreadsheet, _quantity=3, **kwargs)

        spreadsheet = baker.prepare(StateSpreadsheet, **kwargs)
        assert 3 == StateSpreadsheet.objects.filter_older_versions(spreadsheet).count()

        spreadsheet.save()
        spreadsheet.refresh_from_db()
        assert 3 == StateSpreadsheet.objects.filter_older_versions(spreadsheet).count()

    @patch('covid19.signals.process_new_spreadsheet_task', autospec=True)
    def test_cancel_previous_imports_from_user_for_same_state_and_data(
        self, mocked_process_new_spreadsheet
    ):
        kwargs = {
            'date': date.today(), 'user': baker.make(settings.AUTH_USER_MODEL), 'state': 'RJ',
        }

        previous = baker.make(StateSpreadsheet, _quantity=3, **kwargs)
        assert all([not p.cancelled for p in previous])

        spreadsheet = baker.make(StateSpreadsheet, **kwargs)
        new_spreadsheet_imported_signal.send(sender=self, spreadsheet=spreadsheet)
        spreadsheet.refresh_from_db()
        assert not spreadsheet.cancelled

        for prev in previous:
            prev.refresh_from_db()
            assert prev.cancelled

        mocked_process_new_spreadsheet.delay.assert_called_once_with(spreadsheet_pk=spreadsheet.pk)
