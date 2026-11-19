import { ChevronDown, Dna } from 'lucide-react'
import { useId, useState } from 'react'
import type { Phototype } from '../api/types'

interface Props {
  phototypes: Phototype[]
  value: string | null
  onChange: (code: string | null) => void
}

/** Linha opcional "Seu tipo de pele" (fototipo de Fitzpatrick), salva no navegador. */
export function PhototypePicker({ phototypes, value, onChange }: Props) {
  const id = useId()
  const [open, setOpen] = useState(false)
  const current = phototypes.find((p) => p.code === value)

  return (
    <section className="rounded-3xl bg-white p-4 shadow-sm">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={`${id}-panel`}
        onClick={() => setOpen((o) => !o)}
        className="flex min-h-11 w-full items-center justify-between gap-2 text-left focus-visible:outline-3 focus-visible:outline-blue-600"
      >
        <span className="flex items-center gap-2 font-semibold">
          <Dna aria-hidden="true" size={20} />
          Seu tipo de pele
          <span className="font-normal text-neutral-700">
            {current ? `· Tipo ${current.code}` : '· opcional'}
          </span>
        </span>
        <ChevronDown aria-hidden="true" size={20} className={open ? 'rotate-180' : ''} />
      </button>

      {open && (
        <div id={`${id}-panel`} className="mt-3">
          <fieldset>
            <legend className="text-sm text-neutral-700">
              Escolha a descrição mais parecida com a sua pele para estimar em quanto tempo ela pode
              queimar.
            </legend>
            <div className="mt-2 flex flex-col gap-1">
              {phototypes.map((p) => (
                <label
                  key={p.code}
                  className="flex min-h-11 cursor-pointer items-center gap-3 rounded-xl px-2 hover:bg-neutral-50 has-[:focus-visible]:outline-3 has-[:focus-visible]:outline-blue-600"
                >
                  <input
                    type="radio"
                    name={`${id}-phototype`}
                    checked={value === p.code}
                    onChange={() => onChange(p.code)}
                    className="size-5 accent-neutral-900"
                  />
                  <span>
                    <strong>Tipo {p.code}</strong> – {p.description}
                  </span>
                </label>
              ))}
              <label className="flex min-h-11 cursor-pointer items-center gap-3 rounded-xl px-2 hover:bg-neutral-50 has-[:focus-visible]:outline-3 has-[:focus-visible]:outline-blue-600">
                <input
                  type="radio"
                  name={`${id}-phototype`}
                  checked={value === null}
                  onChange={() => onChange(null)}
                  className="size-5 accent-neutral-900"
                />
                Prefiro não informar
              </label>
            </div>
          </fieldset>
          <p className="mt-3 text-sm text-neutral-700">
            O tipo de pele tem forte componente genético: variantes do gene <em>MC1R</em>, por
            exemplo, estão ligadas a pele clara, sardas e maior sensibilidade ao sol. A estimativa
            usa valores típicos da literatura (Fitzpatrick, 1988; Diffey, 1991).
          </p>
        </div>
      )}
    </section>
  )
}
