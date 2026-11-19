import { useHealth } from '../api/hooks'

export function Disclaimer() {
  const health = useHealth()
  const simulated = health.data?.uv_provider === 'simulado'
  return (
    <footer className="mx-auto w-full max-w-5xl px-4 pb-24 text-center text-xs text-neutral-600 md:px-8 md:pb-6">
      Projeto demonstrativo. Não substitui orientação médica.{' '}
      {simulated
        ? 'Sem chave da OpenUV: os valores de UV são simulados para demonstração.'
        : 'Dados: OpenUV e Open-Meteo.'}{' '}
      Histórico e distribuição de fototipos são ilustrativos.
    </footer>
  )
}
