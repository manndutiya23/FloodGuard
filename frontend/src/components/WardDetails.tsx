import type { RiskAssessment, Ward } from '../types'
import RiskPanel from './RiskPanel'
import { EmptyState } from './StatusStates'

interface Props {
  wardCodes: string[]
  selectedWard: string | null
  onSelectWard: (code: string) => void
  ward: Ward | undefined
  assessment: RiskAssessment | undefined
  riskError: boolean
}

export default function WardDetails({ wardCodes, selectedWard, onSelectWard, ward, assessment, riskError }: Props) {
  return (
    <div className="rounded-[10px] border border-line bg-white p-[18px]">
      <label className="flex flex-col gap-1.5 text-xs font-semibold tracking-wide text-muted uppercase">
        Selected ward
        <select
          value={selectedWard ?? ''}
          onChange={(e) => onSelectWard(e.target.value)}
          className="min-h-11 rounded-lg border border-[#9aa7b6] bg-white px-2.5 font-mono text-xl font-semibold tracking-normal text-ink normal-case"
        >
          <option value="" disabled>
            Choose a ward
          </option>
          {wardCodes.map((code) => (
            <option key={code} value={code}>
              {code}
            </option>
          ))}
        </select>
      </label>

      {!selectedWard && <p className="mb-0 text-sm text-muted">Select a ward on the map or from the list.</p>}

      {selectedWard && (
        <div className="mt-3.5 flex flex-col gap-3.5">
          {assessment ? (
            <RiskPanel assessment={assessment} />
          ) : (
            <EmptyState>{riskError ? 'Risk estimate could not be loaded.' : 'No risk estimate for this ward yet.'}</EmptyState>
          )}

          {ward ? (
            <section aria-labelledby="exposure-heading" className="flex flex-col gap-2 rounded-lg border border-line-soft p-3.5">
              <h3 id="exposure-heading" className="m-0 text-[15px]">
                Historical exposure
              </h3>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <div className="font-mono text-[22px] font-semibold">
                    {ward.population_potentially_exposed_within_250m_buffer.toLocaleString('en-IN')}
                  </div>
                  <div className="text-[13px] text-muted">people within 250 m flood buffer</div>
                </div>
                <div>
                  <div className="font-mono text-[22px] font-semibold">
                    {ward.percentage_of_ward_population_potentially_exposed_percent}%
                  </div>
                  <div className="text-[13px] text-muted">of ward population</div>
                </div>
              </div>
              <p className="m-0 text-[13px] text-muted">
                Source: Mumbai Climate Action Plan, Vulnerability Assessment, Table XXVI, p. {ward.source_page ?? 112}.
                Census {ward.underlying_population_data_year} population. Background context, not current flooding.
              </p>
            </section>
          ) : (
            <EmptyState>No historical exposure record for this ward.</EmptyState>
          )}
        </div>
      )}
    </div>
  )
}
