import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { apiGet } from '../api/client'
import { useCities, useCurrent, useForecast, useToday } from '../api/hooks'
import type { City } from '../api/types'
import { BestHours } from '../components/BestHours'
import { CitySelector } from '../components/CitySelector'
import { ErrorState } from '../components/ErrorState'
import { ForecastList } from '../components/ForecastList'
import { LocationPrompt } from '../components/LocationPrompt'
import { ProtectionTips } from '../components/ProtectionTips'
import { Skeleton } from '../components/Skeleton'
import { UvCard } from '../components/UvCard'
import { UvTimeline } from '../components/UvTimeline'
import {
  DEFAULT_CITY_ID,
  getCityId,
  hasAskedLocation,
  markAskedLocation,
  setCityId,
} from '../lib/storage'

function localToday(timeZone: string): string {
  return new Intl.DateTimeFormat('en-CA', { timeZone }).format(new Date())
}

export function HomePage() {
  const [params, setParams] = useSearchParams()
  const fromUrl = Number(params.get('cidade')) || null
  const [cityId, setCity] = useState<number>(fromUrl ?? getCityId() ?? DEFAULT_CITY_ID)
  const [askLocation, setAskLocation] = useState(!hasAskedLocation() && getCityId() === null)
  const [locating, setLocating] = useState(false)
  const [locationError, setLocationError] = useState<string | null>(null)

  const cities = useCities()
  const current = useCurrent(cityId)
  const today = useToday(cityId)
  const forecast = useForecast(cityId)

  const selected = cities.data?.find((c) => c.id === cityId) ?? current.data?.city ?? null
  const timeZone = selected?.timezone ?? 'America/Sao_Paulo'

  const choose = (city: City) => {
    setCity(city.id)
    setCityId(city.id)
    if (params.has('cidade')) setParams({}, { replace: true })
  }

  const useLocation = () => {
    markAskedLocation()
    setAskLocation(false)
    setLocationError(null)
    if (!navigator.geolocation) {
      setLocationError('Seu navegador não informa a localização. Escolha a cidade na busca.')
      return
    }
    setLocating(true)
    navigator.geolocation.getCurrentPosition(
      async ({ coords }) => {
        try {
          choose(
            await apiGet<City>(`/cities/nearest?lat=${coords.latitude}&lng=${coords.longitude}`),
          )
        } catch {
          setLocationError('Não conseguimos achar a cidade mais próxima. Escolha na busca.')
        } finally {
          setLocating(false)
        }
      },
      () => {
        setLocating(false)
        setLocationError('Sem permissão de localização. Mostrando São Paulo; escolha outra cidade na busca.')
      },
      { timeout: 10_000, maximumAge: 600_000 },
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <h1 className="sr-only">Índice UV agora</h1>

      {askLocation && (
        <LocationPrompt
          onAllow={useLocation}
          onDismiss={() => {
            markAskedLocation()
            setAskLocation(false)
          }}
        />
      )}

      <CitySelector
        cities={cities.data ?? []}
        selected={selected}
        onSelect={choose}
        onUseLocation={useLocation}
        locating={locating}
      />
      {locationError && (
        <p role="status" className="text-sm text-neutral-700">
          {locationError}
        </p>
      )}

      {current.isPending ? (
        <Skeleton className="h-72" label="Carregando o UV atual" />
      ) : current.isError ? (
        <ErrorState message="Não foi possível carregar o UV agora." onRetry={() => current.refetch()} />
      ) : (
        <UvCard current={current.data} />
      )}

      <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <div className="flex flex-col gap-4">
          {today.isPending ? (
            <Skeleton className="h-72" label="Carregando a linha do tempo" />
          ) : today.isError ? (
            <ErrorState message="Não foi possível carregar a previsão de hoje." onRetry={() => today.refetch()} />
          ) : (
            <>
              <UvTimeline today={today.data} timeZone={timeZone} />
              <BestHours today={today.data} timeZone={timeZone} />
            </>
          )}
        </div>
        <div className="flex flex-col gap-4">
          {forecast.isPending ? (
            <Skeleton className="h-64" label="Carregando a previsão" />
          ) : forecast.isError ? (
            <ErrorState message="Não foi possível carregar a previsão." onRetry={() => forecast.refetch()} />
          ) : (
            <ForecastList days={forecast.data} today={localToday(timeZone)} />
          )}
          {current.data?.level && <ProtectionTips level={current.data.level.key} />}
        </div>
      </div>
    </div>
  )
}
