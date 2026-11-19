import { LocateFixed, MapPin } from 'lucide-react'
import { useId, useMemo, useState } from 'react'
import type { City } from '../api/types'

interface Props {
  cities: City[]
  selected: City | null
  onSelect: (city: City) => void
  onUseLocation: () => void
  locating?: boolean
}

const normalize = (text: string) =>
  text.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()

/** Combobox acessível (ARIA 1.2) com autocomplete + "Usar minha localização". */
export function CitySelector({ cities, selected, onSelect, onUseLocation, locating }: Props) {
  const id = useId()
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)

  const matches = useMemo(
    () => cities.filter((c) => normalize(c.name).includes(normalize(query.trim()))),
    [cities, query],
  )

  const choose = (city: City) => {
    onSelect(city)
    setQuery('')
    setOpen(false)
  }

  const onKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setOpen(true)
      setActive((i) => Math.min(i + 1, matches.length - 1))
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActive((i) => Math.max(i - 1, 0))
    } else if (event.key === 'Enter' && open && matches[active]) {
      event.preventDefault()
      choose(matches[active])
    } else if (event.key === 'Escape') {
      setOpen(false)
    }
  }

  const listId = `${id}-list`
  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
      <div className="relative flex-1">
        <label htmlFor={`${id}-input`} className="sr-only">
          Buscar cidade
        </label>
        <MapPin
          aria-hidden="true"
          size={18}
          className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-neutral-500"
        />
        <input
          id={`${id}-input`}
          role="combobox"
          aria-expanded={open}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={open && matches[active] ? `${id}-opt-${matches[active].id}` : undefined}
          autoComplete="off"
          placeholder={selected ? `${selected.name} – ${selected.state}` : 'Buscar cidade'}
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            setActive(0)
            setOpen(true)
          }}
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 120)}
          onKeyDown={onKeyDown}
          className="min-h-12 w-full rounded-xl border border-neutral-300 bg-white pr-3 pl-10 text-base font-medium placeholder:text-neutral-800 focus:border-neutral-900 focus:outline-3 focus:outline-blue-600"
        />
        {open && (
          <ul
            id={listId}
            role="listbox"
            aria-label="Cidades"
            className="absolute z-[1100] mt-1 max-h-72 w-full overflow-auto rounded-xl border border-neutral-200 bg-white py-1 shadow-lg"
          >
            {matches.length === 0 && <li className="px-4 py-3 text-neutral-600">Nenhuma cidade encontrada</li>}
            {matches.map((city, index) => (
              <li
                key={city.id}
                id={`${id}-opt-${city.id}`}
                role="option"
                aria-selected={index === active}
                onMouseDown={(e) => {
                  e.preventDefault()
                  choose(city)
                }}
                onMouseEnter={() => setActive(index)}
                className={`flex min-h-11 cursor-pointer items-center px-4 ${
                  index === active ? 'bg-neutral-100' : ''
                }`}
              >
                {city.name} <span className="ml-1 text-neutral-500">– {city.state}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
      <button
        type="button"
        onClick={onUseLocation}
        disabled={locating}
        className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl border border-neutral-300 bg-white px-4 font-semibold hover:bg-neutral-100 focus-visible:outline-3 focus-visible:outline-blue-600 disabled:opacity-60"
      >
        <LocateFixed aria-hidden="true" size={18} />
        {locating ? 'Localizando…' : 'Usar minha localização'}
      </button>
    </div>
  )
}
