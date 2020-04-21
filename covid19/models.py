from copy import deepcopy
from pathlib import Path
from localflavor.br.br_states import STATE_CHOICES

from django.contrib.auth import get_user_model
from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField


def format_spreadsheet_name(instance, filename):
    # file will be uploaded to MEDIA_ROOT/{uf}/casos-{uf}-{date}-{username}-{file_no}.{extension}"
    # where {file_no} is the number of uploaded files from that user for the same pair of state
    # and date. this is necessary to avoid other users from overwriting other spreadsheets
    uf = instance.state
    date = instance.date.isoformat()
    user = instance.user.username
    file_no = StateSpreadsheet.objects.filter_older_versions(instance).count() + 1
    suffix = Path(filename).suffix
    return f'covid19/{uf}/casos-{uf}-{date}-{user}-{file_no}{suffix}'  # noqa


class StateSpreadsheetQuerySet(models.QuerySet):

    def filter_older_versions(self, spreadsheet):
        qs = self.from_user(spreadsheet.user).from_state(spreadsheet.state).filter(
            date=spreadsheet.date,
        )
        if spreadsheet.id:
            qs = qs.exclude(id=spreadsheet.id)
        return qs

    def from_user(self, user):
        return self.filter(user=user)

    def from_state(self, state):
        return self.filter(state__iexact=state)

    def cancel_older_versions(self, spreadsheet):
        return self.filter_older_versions(spreadsheet).update(cancelled=True)

    def filter_active(self):
        return self.filter(cancelled=False)


def default_data_json():
    return {
        "table": [],
        "errors": [],
        "warnings": [],
    }


class StateSpreadsheet(models.Model):
    UPLOADED, CHECK_FAILED, DEPLOYED = 1, 2, 3
    STATUS_CHOICES = (
        (UPLOADED, "uploaded"),
        (CHECK_FAILED, "check-failed"),
        (DEPLOYED, "deployed"),
    )

    objects = StateSpreadsheetQuerySet.as_manager()

    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(get_user_model(), null=False, blank=False, on_delete=models.PROTECT)
    date = models.DateField(null=False, blank=False)
    state = models.CharField(max_length=2, null=False, blank=False, choices=STATE_CHOICES)
    file = models.FileField(upload_to=format_spreadsheet_name)

    boletim_urls = ArrayField(
        models.TextField(), null=False,
        blank=False, help_text="Lista de URLs do(s) boletim(s)"
    )
    boletim_notes = models.CharField(
        max_length=1023, default='', blank=True,
        help_text='Observações no boletim como "depois de publicar o boletim a secretaria postou no Twitter que teve mais uma morte".'  # noqa
    )

    # status da planilha: só aceitaremos planilhas sem erros, então quando ela
    # é subida, inicia-se um processo em background de checá-la conforme outra
    # planilha pro mesmo estado pra mesma data - esse worker é quem mudará o
    # status, o padrao qnd sobe a planilha e não tem erros é uploaded
    # (configurar celery ou rq)
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=UPLOADED)

    # dados da planilha depois de parseada no form, já em JSON, pro worker não
    # precisar ler o arquivo (o validador da planilha no form vai ter que fazer
    # essa leitura, então ele faz, se estiver tudo ok já salva nesse campo pro
    # worker já trabalhar com os dados limpos e normalizados)
    data = JSONField(default=default_data_json)

    # por padrao é False, mas vira True se um mesmo usuário subir uma planilha
    # pro mesmo estado pra mesma data (ele cancela o upload anterior pra essa
    # data/estado automaticamente caso suba uma atualizacao)
    cancelled = models.BooleanField(default=False)

    def __str__(self):
        active = 'Ativa' if not self.cancelled else 'Cancelada'
        return f'Planilha {active}: {self.state} - {self.date} por {self.user}'

    @property
    def table_data(self):
        return deepcopy(self.data['table'])

    @table_data.setter
    def table_data(self, data):
        self.data['table'] = deepcopy(data)

    @property
    def warnings(self):
        return deepcopy(self.data['warnings'])

    @warnings.setter
    def warnings(self, data):
        self.data['warnings'] = data

    @property
    def errors(self):
        return deepcopy(self.data['errors'])

    @errors.setter
    def errors(self, data):
        self.data['errors'] = data
        self.status = StateSpreadsheet.CHECK_FAILED

    def get_data_from_city(self, ibge_code):
        if ibge_code:  # ibge_code = None match for undefined data
            ibge_code = int(ibge_code)
        try:
            return [d for d in self.table_data if d['city_ibge_code'] == ibge_code][0]
        except IndexError:
            return None

    def get_total_data(self):
        try:
            return [d for d in self.table_data if d['place_type'] == 'state'][0]
        except IndexError:
            return None
