from django.core.management.base import BaseCommand
from django.utils import timezone
from impressoras.models import AgendamentoColeta
from impressoras.snmp_collector import coletar_impressora, coletar_todas


class Command(BaseCommand):
    help = 'Executa agendamentos de coleta SNMP vencidos'

    def handle(self, *args, **options):
        now = timezone.now()
        pendentes = AgendamentoColeta.objects.filter(ativo=True, proxima_execucao__lte=now).select_related('impressora')

        if not pendentes.exists():
            self.stdout.write('Nenhum agendamento vencido.')
            return

        for ag in pendentes:
            try:
                if ag.todas:
                    resultados = coletar_todas()
                    ok = sum(1 for r in resultados if r['ok'])
                    self.stdout.write(self.style.SUCCESS(
                        f'[{ag.nome}] Todas: {ok}/{len(resultados)} OK'
                    ))
                else:
                    leitura = coletar_impressora(ag.impressora)
                    if leitura.erro:
                        self.stdout.write(self.style.WARNING(
                            f'[{ag.nome}] {ag.impressora.nome}: ERRO — {leitura.erro}'
                        ))
                    else:
                        self.stdout.write(self.style.SUCCESS(
                            f'[{ag.nome}] {ag.impressora.nome}: {leitura.valor_contador} págs'
                        ))

                ag.ultima_execucao = now
                ag.proxima_execucao = ag.calcular_proxima()
                ag.save(update_fields=['ultima_execucao', 'proxima_execucao'])

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'[{ag.nome}] Falha: {e}'))
