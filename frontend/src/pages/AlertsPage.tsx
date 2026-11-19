import { BellRing, Minus, Plus, Trash2 } from 'lucide-react'
import { useState } from 'react'
import {
  useAlertTriggers,
  useAlerts,
  useCities,
  useCreateAlert,
  useDeleteAlert,
  useUpdateAlert,
} from '../api/hooks'
import type { Alert } from '../api/types'
import { ErrorState } from '../components/ErrorState'
import { Skeleton } from '../components/Skeleton'
import { UvBadge } from '../components/UvBadge'
import { hourLabel } from '../lib/format'

const MIN = 1
const MAX = 15

const focusRing = 'focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-blue-600'

function AlertForm() {
  const cities = useCities()
  const create = useCreateAlert()
  const [cityId, setCityId] = useState<number | ''>('')
  const [threshold, setThreshold] = useState(8)
  const clamp = (v: number) => Math.min(MAX, Math.max(MIN, v))

  const submit = (event: React.FormEvent) => {
    event.preventDefault()
    if (cityId === '') return
    create.mutate({ city_id: cityId, threshold })
  }

  return (
    <form onSubmit={submit} className="rounded-3xl bg-white p-5 shadow-sm" aria-labelledby="new-alert-title">
      <h2 id="new-alert-title" className="text-lg font-bold">
        Novo alerta
      </h2>
      <div className="mt-3 flex flex-wrap items-end gap-3 text-lg">
        <span className="pb-2">Me avise quando o UV passar de</span>
        <div className="flex items-center gap-1">
          <button
            type="button"
            aria-label="Diminuir limite"
            onClick={() => setThreshold((t) => clamp(t - 1))}
            className={`flex size-11 items-center justify-center rounded-xl border border-neutral-300 ${focusRing}`}
          >
            <Minus aria-hidden="true" size={18} />
          </button>
          <label className="sr-only" htmlFor="threshold">
            Limite de UV
          </label>
          <input
            id="threshold"
            type="number"
            min={MIN}
            max={MAX}
            value={threshold}
            onChange={(e) => setThreshold(clamp(Number(e.target.value) || MIN))}
            className="min-h-11 w-16 rounded-xl border border-neutral-300 text-center font-bold tabular-nums focus:outline-3 focus:outline-blue-600"
          />
          <button
            type="button"
            aria-label="Aumentar limite"
            onClick={() => setThreshold((t) => clamp(t + 1))}
            className={`flex size-11 items-center justify-center rounded-xl border border-neutral-300 ${focusRing}`}
          >
            <Plus aria-hidden="true" size={18} />
          </button>
        </div>
        <span className="pb-2">em</span>
        <label className="sr-only" htmlFor="alert-city">
          Cidade
        </label>
        <select
          id="alert-city"
          required
          value={cityId}
          onChange={(e) => setCityId(e.target.value ? Number(e.target.value) : '')}
          className="min-h-11 rounded-xl border border-neutral-300 bg-white px-3 font-medium focus:outline-3 focus:outline-blue-600"
        >
          <option value="">Escolha a cidade</option>
          {(cities.data ?? []).map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>
      <button
        type="submit"
        disabled={create.isPending || cityId === ''}
        className={`mt-4 min-h-11 rounded-xl bg-neutral-900 px-5 font-semibold text-white disabled:opacity-50 ${focusRing}`}
      >
        Criar alerta
      </button>
      {create.isError && (
        <p role="alert" className="mt-2 text-sm text-red-800">
          Não foi possível criar o alerta. Tente de novo.
        </p>
      )}
    </form>
  )
}

function AlertItem({ alert }: { alert: Alert }) {
  const update = useUpdateAlert()
  const remove = useDeleteAlert()
  const label = `Alerta de ${alert.city.name} acima de ${alert.threshold}`
  return (
    <li className="flex min-h-14 items-center gap-3 px-4 py-2">
      <div className="flex-1">
        <p className="font-semibold">{alert.city.name}</p>
        <p className="text-sm text-neutral-700">
          Quando passar de <strong>{alert.threshold}</strong>
          {alert.last_triggered_at && ' · último aviso ' + new Date(alert.last_triggered_at).toLocaleDateString('pt-BR')}
        </p>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={alert.active}
        aria-label={label}
        onClick={() => update.mutate({ id: alert.id, active: !alert.active })}
        className={`relative inline-flex h-8 w-14 shrink-0 items-center rounded-full transition-colors ${focusRing} ${
          alert.active ? 'bg-neutral-900' : 'bg-neutral-300'
        }`}
      >
        <span
          aria-hidden="true"
          className={`inline-block size-6 rounded-full bg-white shadow transition-transform ${
            alert.active ? 'translate-x-7' : 'translate-x-1'
          }`}
        />
        <span className="sr-only">{alert.active ? 'Ligado' : 'Desligado'}</span>
      </button>
      <button
        type="button"
        aria-label={`Excluir ${label.toLowerCase()}`}
        onClick={() => remove.mutate(alert.id)}
        className={`flex size-11 items-center justify-center rounded-xl text-neutral-600 hover:bg-neutral-100 ${focusRing}`}
      >
        <Trash2 aria-hidden="true" size={18} />
      </button>
    </li>
  )
}

export function AlertsPage() {
  const alerts = useAlerts()
  const triggers = useAlertTriggers()

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Alertas</h1>
        <p className="text-neutral-700">Receba um aviso aqui quando o UV passar do limite escolhido.</p>
      </div>

      <AlertForm />

      <section aria-labelledby="my-alerts-title">
        <h2 id="my-alerts-title" className="mb-2 text-lg font-bold">
          Meus alertas
        </h2>
        {alerts.isPending ? (
          <Skeleton className="h-24" label="Carregando alertas" />
        ) : alerts.isError ? (
          <ErrorState message="Não foi possível carregar seus alertas." onRetry={() => alerts.refetch()} />
        ) : alerts.data.length === 0 ? (
          <p className="rounded-3xl bg-white p-5 text-neutral-700 shadow-sm">Você ainda não criou alertas.</p>
        ) : (
          <ul className="divide-y divide-neutral-100 rounded-3xl bg-white shadow-sm">
            {alerts.data.map((alert) => (
              <AlertItem key={alert.id} alert={alert} />
            ))}
          </ul>
        )}
      </section>

      <section aria-labelledby="triggers-title">
        <h2 id="triggers-title" className="mb-2 flex items-center gap-2 text-lg font-bold">
          <BellRing aria-hidden="true" size={20} /> Disparos de hoje
        </h2>
        {triggers.data && triggers.data.length > 0 ? (
          <ul className="divide-y divide-neutral-100 rounded-3xl bg-white shadow-sm">
            {triggers.data.map((t) => (
              <li key={`${t.alert_id}-${t.triggered_at}`} className="flex min-h-12 items-center gap-3 px-4 py-2">
                <UvBadge uv={t.uv} size="sm" showLabel={false} />
                <span className="flex-1">
                  UV passou de {t.threshold} em <strong>{t.city_name}</strong> às{' '}
                  {hourLabel(t.triggered_at, 'America/Sao_Paulo')}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="rounded-3xl bg-white p-5 text-neutral-700 shadow-sm">Nenhum alerta disparado hoje.</p>
        )}
      </section>
    </div>
  )
}
