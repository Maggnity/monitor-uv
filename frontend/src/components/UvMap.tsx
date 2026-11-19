import L from 'leaflet'
import { useMemo } from 'react'
import { MapContainer, Marker, TileLayer } from 'react-leaflet'
import type { MapPoint } from '../api/types'
import { UV_LEVELS } from '../theme/uvScale'


function markerIcon(point: MapPoint): L.DivIcon {
  const key = point.level?.key
  const bg = key ? UV_LEVELS[key].bg : '#A3A3A3'
  const fg = key ? UV_LEVELS[key].fg : '#171717'
  const text = point.uv === null ? '–' : String(Math.round(point.uv))
  return L.divIcon({
    className: '',
    iconSize: [44, 44],
    iconAnchor: [22, 22],
    html: `<span style="display:flex;align-items:center;justify-content:center;width:44px;height:44px;border-radius:9999px;background:${bg};color:${fg};font:800 17px 'Inter Variable',sans-serif;border:3px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.35)">${text}</span>`,
  })
}

interface Props {
  points: MapPoint[]
  onSelect: (point: MapPoint) => void
}

export function UvMap({ points, onSelect }: Props) {
  const icons = useMemo(() => new Map(points.map((p) => [p.city_id, markerIcon(p)])), [points])
  const bounds = useMemo(
    () => L.latLngBounds(points.map((p) => [p.lat, p.lng] as [number, number])).pad(0.25),
    // Enquadra só na primeira carga; trocar o filtro não move o mapa.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  )
  return (
    <MapContainer
      bounds={bounds}
      minZoom={3}
      scrollWheelZoom={false}
      className="h-full w-full"
      aria-label="Mapa das cidades monitoradas"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {points.map((point) => (
        <Marker
          key={point.city_id}
          position={[point.lat, point.lng]}
          icon={icons.get(point.city_id)}
          keyboard
          title={`${point.name}: UV ${point.uv === null ? 'sem dado' : Math.round(point.uv)}${
            point.level ? `, ${point.level.label}` : ''
          }`}
          alt={`${point.name}: UV ${point.uv === null ? 'sem dado' : Math.round(point.uv)}`}
          eventHandlers={{ click: () => onSelect(point) }}
        />
      ))}
    </MapContainer>
  )
}
