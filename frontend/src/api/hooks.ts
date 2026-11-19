import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiGet, apiSend } from './client'
import type {
  Alert,
  AlertTrigger,
  City,
  Compare,
  Current,
  ForecastDay,
  History,
  MapPoint,
  MapWhen,
  Period,
  Phototype,
  Today,
} from './types'

const FIVE_MINUTES = 5 * 60_000

export const useCities = () =>
  useQuery({ queryKey: ['cities'], queryFn: () => apiGet<City[]>('/cities'), staleTime: Infinity })

export const useCurrent = (cityId: number | null, phototype?: string | null) =>
  useQuery({
    queryKey: ['current', cityId, phototype ?? null],
    queryFn: () =>
      apiGet<Current>(
        `/cities/${cityId}/current${phototype ? `?phototype=${encodeURIComponent(phototype)}` : ''}`,
      ),
    enabled: cityId !== null,
    refetchInterval: FIVE_MINUTES,
  })

export const useToday = (cityId: number | null) =>
  useQuery({
    queryKey: ['today', cityId],
    queryFn: () => apiGet<Today>(`/cities/${cityId}/today`),
    enabled: cityId !== null,
    refetchInterval: FIVE_MINUTES,
  })

export const useForecast = (cityId: number | null) =>
  useQuery({
    queryKey: ['forecast', cityId],
    queryFn: () => apiGet<ForecastDay[]>(`/cities/${cityId}/forecast`),
    enabled: cityId !== null,
  })

export const useHistory = (cityId: number | null, period: Period) =>
  useQuery({
    queryKey: ['history', cityId, period],
    queryFn: () => apiGet<History>(`/cities/${cityId}/history?period=${period}`),
    enabled: cityId !== null,
  })

export const useCompare = (cityIds: number[]) =>
  useQuery({
    queryKey: ['compare', cityIds],
    queryFn: () =>
      apiGet<Compare>(`/compare${cityIds.length ? `?city_ids=${cityIds.join(',')}` : ''}`),
    refetchInterval: FIVE_MINUTES,
  })

export const useMap = (when: MapWhen) =>
  useQuery({
    queryKey: ['map', when],
    queryFn: () => apiGet<MapPoint[]>(`/map?when=${when}`),
    refetchInterval: FIVE_MINUTES,
  })

export const usePhototypes = () =>
  useQuery({
    queryKey: ['phototypes'],
    queryFn: () => apiGet<Phototype[]>('/phototypes'),
    staleTime: Infinity,
    retry: false,
  })

export const useAlerts = () =>
  useQuery({ queryKey: ['alerts'], queryFn: () => apiGet<Alert[]>('/alerts') })

export const useAlertTriggers = () =>
  useQuery({
    queryKey: ['alert-triggers'],
    queryFn: () => apiGet<AlertTrigger[]>('/alerts/triggers'),
    refetchInterval: FIVE_MINUTES,
  })

function useAlertMutation<TVars>(fn: (vars: TVars) => Promise<unknown>) {
  const client = useQueryClient()
  return useMutation({
    mutationFn: fn,
    onSuccess: () => client.invalidateQueries({ queryKey: ['alerts'] }),
  })
}

export const useCreateAlert = () =>
  useAlertMutation((body: { city_id: number; threshold: number }) =>
    apiSend<Alert>('POST', '/alerts', body),
  )

export const useUpdateAlert = () =>
  useAlertMutation(({ id, ...body }: { id: number; active?: boolean; threshold?: number }) =>
    apiSend<Alert>('PATCH', `/alerts/${id}`, body),
  )

export const useDeleteAlert = () =>
  useAlertMutation((id: number) => apiSend<void>('DELETE', `/alerts/${id}`))
